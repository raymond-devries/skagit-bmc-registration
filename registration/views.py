from django.shortcuts import render
from django.views.generic.edit import FormView
from registration.forms import BMCRegistrationForm
from django.contrib.auth.forms import UserCreationForm


class UserRegistrationView(FormView):
    template_name = "registration/signup.html"
    form_class = UserCreationForm
    success_url = "/home"


def home(request):
    return render(request, "bmc_registration/home.html")


class BMCRegistrationView(FormView):
    template_name = "bmc_registration/bmc_registration.html"
    form_class = BMCRegistrationForm
    success_url = "/home"

