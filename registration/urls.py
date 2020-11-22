from registration import views
from django.urls import path

urlpatterns = [
    path("", views.home, name="home"),
    path("bmc-registration", views.BMCRegistrationView.as_view(), name="BMCRegistration")
]
