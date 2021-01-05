from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, FormView, TemplateView

from registration import models
from registration.forms import RegistrationForm, SignUpForm


class UserRegistrationView(SuccessMessageMixin, CreateView):
    template_name = "registration/signup.html"
    form_class = SignUpForm
    success_url = reverse_lazy("home")
    success_message = "You have successfully created an account you can now login"


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
        context["user_courses"] = models.Course.objects.filter(
            participants=self.request.user
        )
        context["user_waitlist"] = models.Course.objects.filter(
            waitlist__user=self.request.user
        )

        return context


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


class CartView(LoginRequiredMixin, TemplateView):
    template_name = "bmc_registration/cart.html"
