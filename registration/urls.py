from registration import views
from django.urls import path

urlpatterns = [
    path("", views.home, name="home"),
    path("bmc_registration", views.BMCRegistrationView.as_view(), name="BMCRegistration"),
    path("signup", views.UserRegistrationView.as_view(), name="signup")
]
