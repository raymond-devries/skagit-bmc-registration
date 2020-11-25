from django.urls import path

from registration import views

urlpatterns = [
    path("", views.Home.as_view(), name="home"),
    path(
        "bmc_registration/", views.BMCRegistrationView.as_view(), name="BMCRegistration"
    ),
    path("signup/", views.UserRegistrationView.as_view(), name="signup"),
]
