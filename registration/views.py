from django.shortcuts import render
from django.views.generic.edit import FormView
from registration.forms import BMCRegistrationForm


def home(request):
    return render(request, "registration/home.html")


class BMCRegistrationView(FormView):
    template_name = "registration/bmc_registration.html"
    form_class = BMCRegistrationForm
    success_url = "/home"
