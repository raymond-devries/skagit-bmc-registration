import datetime

import stripe
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import mixins, permissions, views, viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from registration import models, serializers
from SkagitRegistration import settings


class ListEligibleCoursesView(viewsets.ReadOnlyModelViewSet):
    serializer_class = serializers.CourseTypeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return models.UserCart.objects.get(user=user).eligible_courses.filter(
            visible=True
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["user"] = self.request.user
        return context


class CartItemView(
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return models.UserCart.objects.get(user=user).cartitem_set.all()

    def perform_create(self, serializer):
        serializer.save(cart=models.UserCart.objects.get(user=self.request.user))

    def get_serializer_class(self):
        if self.action == "list":
            return serializers.CartItemListSerializer
        return serializers.CartItemSerializer


class CartCostView(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, *args, **kwargs):
        cart = models.UserCart.objects.get(user=request.user)
        serialized_data = serializers.CartCostSerializer(cart).data
        return Response(serialized_data)


class WaitListView(
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = serializers.WaitListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return models.WaitList.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@api_view(["POST"])
def create_checkout_session(request):
    if request.method == "POST":
        if not request.user.profile.is_eligible_for_registration:
            return Response("User is not eligible for registration", status=403)
        cart = models.UserCart.objects.get(user=request.user)
        cart_items = models.CartItem.objects.filter(cart=cart)
        discounts = []
        coupon_id = None
        if pi_discount := models.PreviousStudentDiscount.objects.filter(
            email=request.user.email
        ).first():
            coupon = stripe.Coupon.create(
                percent_off=pi_discount.discount, name="Previous student discount"
            )
            discounts.append({"coupon": coupon.stripe_id})
            coupon_id = coupon.id
        line_items = []
        for item in cart_items:
            line_items.append(
                {
                    "price_data": {
                        "currency": "usd",
                        "unit_amount": item.course.type.cost,
                        "product_data": {
                            "name": item.course.type.name,
                            "metadata": {
                                "course_id": item.course.id,
                                "cart_item_id": item.id,
                                "coupon_id": coupon_id,
                            },
                        },
                    },
                    "quantity": 1,
                }
            )

        checkout_session = stripe.checkout.Session.create(
            customer=request.user.profile.stripe_customer_id,
            metadata={"user_id": request.user.id},
            payment_method_types=["card"],
            line_items=line_items,
            mode="payment",
            discounts=discounts,
            success_url=request.build_absolute_uri(reverse("registration_home")),
            cancel_url=request.build_absolute_uri(reverse("cart")),
        )
        return Response({"id": checkout_session.id})


@csrf_exempt
def stripe_checkout_webhook(request):
    payload = request.body
    sig_header = request.META["HTTP_STRIPE_SIGNATURE"]

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_ENDPOINT_SECRET
        )
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]

        line_items = stripe.checkout.Session.list_line_items(session.stripe_id)
        product_ids = [(item.price.product, item.price.id) for item in line_items]
        courses = []
        for product_id, price_id in product_ids:
            product = stripe.Product.retrieve(product_id)
            course_id = product.metadata.get("course_id")
            if course_id is None:
                return HttpResponse(
                    "NOT PROCESSED: No course ID was provided", status=204
                )
            courses.append(
                {
                    "course_id": course_id,
                    "product_id": product_id,
                    "price_id": price_id,
                    "coupon_id": product.metadata.get("coupon_id", ""),
                }
            )

        fulfill_order(
            courses,
            session.metadata.user_id,
            checkout_session_id=session.stripe_id,
            payment_intent_id=session.payment_intent,
        )

    elif event["type"] == "invoice.paid":
        invoice = event["data"]["object"]
        wait_list_invoice = models.WaitListInvoice.objects.get(invoice_id=invoice.id)
        wait_list_invoice.paid = True
        wait_list_invoice.save()
        wait_list_invoice.course.capacity += 1
        wait_list_invoice.course.save()
        price = invoice.lines.data[0].price
        courses = [
            {
                "course_id": wait_list_invoice.course.id,
                "product_id": price.product,
                "price_id": price.id,
                "coupon_id": "",
            }
        ]
        fulfill_order(
            courses,
            wait_list_invoice.user.id,
            invoice_id=invoice.id,
            payment_intent_id=invoice.payment_intent,
        )

    return HttpResponse(status=200)


def fulfill_order(
    courses, user_id, checkout_session_id="", invoice_id="", payment_intent_id=""
):
    user = User.objects.get(id=user_id)
    cart = models.UserCart.objects.get(user=user)
    models.CartItem.objects.filter(cart=cart).delete()
    payment_record = models.PaymentRecord.objects.create(
        user=user,
        checkout_session_id=checkout_session_id,
        payment_intent_id=payment_intent_id,
        invoice_id=invoice_id,
    )
    for course_data in courses:
        course = models.Course.objects.get(id=course_data["course_id"])
        course.participants.add(user)
        models.CourseBought.objects.create(
            payment_record=payment_record,
            course=course,
            product_id=course_data["product_id"],
            price_id=course_data["price_id"],
            coupon_id=course_data["coupon_id"],
        )


class AddCoursesView(views.APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, *args, **kwargs):
        for course_type in request.data:
            try:
                gear = course_type["all_gear"]
                for item in gear:
                    models.GearItem.objects.create(type=None, item=item)
                continue
            except KeyError:
                pass

            try:
                requirement = models.CourseType.objects.get(
                    name=course_type["requirement"]
                )
            except models.CourseType.DoesNotExist:
                requirement = None

            created_course_type = models.CourseType.objects.create(
                name=course_type["name"],
                description=course_type["description"],
                abbreviation=course_type["abbreviation"],
                requirement=requirement,
                cost=course_type["cost"],
            )

            for course in course_type["courses"]:
                created_course = models.Course.objects.create(
                    type=created_course_type,
                    specifics=course["specifics"],
                    capacity=course["capacity"],
                )

                for date in course["course_dates"]:
                    start = datetime.datetime.strptime(
                        date["start"], "%Y-%m-%dT%H:%M:%S.%fZ"
                    )
                    end = datetime.datetime.strptime(
                        date["end"], "%Y-%m-%dT%H:%M:%S.%fZ"
                    )
                    models.CourseDate.objects.create(
                        course=created_course, name=date["name"], start=start, end=end
                    )

            for item in course_type["gear_list"]:
                models.GearItem.objects.create(type=created_course_type, item=item)

        return Response("Added the courses")
