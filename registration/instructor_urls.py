from django.urls import path

from registration import views

url_patterns = [
    path(
        "current-registrations/",
        views.CurrentRegistrationsView.as_view(),
        name="current_registrations",
    )
]
