from django.urls import include, path

from registration import sign_up_views

urlpatterns = [
    path("signup/", sign_up_views.Signup.as_view(), name="signup"),
    path(
        "account_activation_sent/",
        sign_up_views.AccountActivationSent.as_view(),
        name="account_activation_sent",
    ),
    path(
        "activate/(<uib64>/(<token>/", sign_up_views.Activate.as_view(), name="activate"
    ),
]
