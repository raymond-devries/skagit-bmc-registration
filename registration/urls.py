from django.urls import path

from registration import views

urlpatterns = [
    path("", views.Home.as_view(), name="home"),
    path(
        "bmc_registration_form/",
        views.RegistrationInfoForm.as_view(),
        name="registration_info_form",
    ),
    path(
        "registration_home", views.RegistrationHome.as_view(), name="registration_home"
    ),
    path("signup/", views.UserRegistrationView.as_view(), name="signup"),
]
