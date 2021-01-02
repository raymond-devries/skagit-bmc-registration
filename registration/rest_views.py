import stripe
from django.http import HttpResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import mixins, permissions, viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from registration import models, serializers
from SkagitRegistration import settings

stripe.api_key = settings.STRIPE_API_KEY


class ListEligibleCoursesView(viewsets.ReadOnlyModelViewSet):
    serializer_class = serializers.CourseTypeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return models.UserCart.objects.get(user=user).eligible_courses

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
        cart = models.UserCart.objects.get(user=request.user)
        cart_items = models.CartItem.objects.filter(cart=cart)
        if cart.discount is not None:
            discounts = [{"coupon": cart.discount.stripe_id}]
        else:
            discounts = []
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
                            },
                        },
                    },
                    "quantity": 1,
                }
            )

        checkout_session = stripe.checkout.Session.create(
            customer_email=request.user.email,
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

        print(session)

    return HttpResponse(status=200)
