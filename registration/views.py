from django.contrib.auth.mixins import LoginRequiredMixin
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


class BMCRegistrationView(LoginRequiredMixin, CreateView):
    template_name = "bmc_registration/bmc_registration.html"
    form_class = BMCRegistrationForm
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

