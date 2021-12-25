import stripe
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import FormView, TemplateView

from registration import models
from registration.forms import RegistrationForm
from SkagitRegistration import settings


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "bmc_registration/profile.html"


class Home(TemplateView):
    template_name = "bmc_registration/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["discounts"] = models.Discount.objects.all()
        return context


class AvailableCoursesView(TemplateView):
    template_name = "bmc_registration/available_courses.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["available_courses"] = models.CourseType.objects.filter(
            visible=True
        ).order_by("name")

        return context


class RegistrationHome(LoginRequiredMixin, TemplateView):
    template_name = "bmc_registration/registration_home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["registration_complete"] = models.RegistrationForm.objects.filter(
            user=self.request.user
        ).exists()
        context["registration_settings"] = models.RegistrationSettings.objects.first()
        context["user_courses"] = models.Course.objects.filter(
            participants=self.request.user
        )
        context["user_waitlist"] = models.Course.objects.filter(
            waitlist__user=self.request.user
        )

        return context


@login_required
def refund(request, course_pk):
    course_bought = get_object_or_404(
        models.CourseBought,
        course__participants=request.user,
        course=course_pk,
        refunded=False,
    )
    refund_eligible = course_bought.refund_eligible
    context = {"refund_eligible": refund_eligible, "course": course_bought.course}

    if refund_eligible:
        purchase_price = stripe.Price.retrieve(course_bought.price_id)["unit_amount"]
        context["purchase_price"] = models.human_readable_cost(purchase_price)
        refund_amount = (
            purchase_price
            - models.RegistrationSettings.objects.first().cancellation_fee
        )
        context["refund_amount"] = models.human_readable_cost(refund_amount)

        if request.method == "POST":
            refund = stripe.Refund.create(
                payment_intent=course_bought.payment_record.payment_intent_id,
                idempotency_key=str(course_bought.id),
            )
            course_bought.refund_id = refund["id"]
            course_bought.refunded = True
            course_bought.save()
            course_bought.course.participants.remove(request.user)
            redirect("registration_home")

    return render(request, "bmc_registration/refund.html", context)


class RegistrationInfoForm(LoginRequiredMixin, FormView):
    template_name = "bmc_registration/registration_form.html"
    form_class = RegistrationForm
    success_url = reverse_lazy("registration_home")

    def get_form(self, form_class=None):
        try:
            instance = models.RegistrationForm.objects.get(user=self.request.user)
            form = self.get_form_class()
            return form(instance=instance, **self.get_form_kwargs())
        except models.RegistrationForm.DoesNotExist:
            return super().get_form(form_class=form_class)

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.save()
        return super().form_valid(form)


class CourseSignUp(LoginRequiredMixin, TemplateView):
    template_name = "bmc_registration/course_sign_up.html"

    def get(self, request, *args, **kwargs):
        if not models.RegistrationForm.objects.filter(user=self.request.user).exists():
            return redirect(reverse_lazy("registration_home"))
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["discounts"] = models.Discount.objects.all()
        return context


class CartView(LoginRequiredMixin, TemplateView):
    template_name = "bmc_registration/cart.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["registration_settings"] = models.RegistrationSettings.objects.first()
        context["stripe_public_api_key"] = settings.STRIPE_PUBLIC_API_KEY
        return context


class GearListsView(TemplateView):
    template_name = "bmc_registration/gear_list.html"

    def get_context_data(self, *args, object_list=None, **kwargs):
        context = super().get_context_data(object_list=None, **kwargs)
        context["gear_item_all"] = models.GearItem.objects.filter(type=None)
        context["courses"] = models.CourseType.objects.filter(visible=True).order_by(
            "name"
        )
        return context
