from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView
from registration.forms import BMCRegistrationForm, SignUpForm
from django.contrib.messages.views import SuccessMessageMixin


class UserRegistrationView(SuccessMessageMixin, CreateView):
    template_name = "registration/signup.html"
    form_class = SignUpForm
    success_url = reverse_lazy("home")
    success_message = "You have successfully created an account you can now login"


class Home(TemplateView):
    template_name = "bmc_registration/home.html"


class BMCRegistrationView(CreateView):
    template_name = "bmc_registration/bmc_registration.html"
    form_class = BMCRegistrationForm
    success_url = reverse_lazy("home")

