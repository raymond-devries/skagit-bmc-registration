from django.urls import path

from registration.instructor import instructor_views

url_patterns = [
    path(
        "current-registrations/",
        instructor_views.CurrentRegistrationsView.as_view(),
        name="current_registrations",
    )
]
