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
    course = get_object_or_404(models.Course, participants=request.user, pk=course_pk)
    return render(request, "bmc_registration/refund.html")


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
