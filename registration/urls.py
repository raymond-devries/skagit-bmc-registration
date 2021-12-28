from django.urls import path

from registration import views

urlpatterns = [
    path("", views.Home.as_view(), name="home"),
    path(
        "available-courses/",
        views.AvailableCoursesView.as_view(),
        name="available_courses",
    ),
    path("gear-lists/", views.GearListsView.as_view(), name="gear_lists"),
    path(
        "registration/form/",
        views.RegistrationInfoForm.as_view(),
        name="registration_info_form",
    ),
    path(
        "registration/home/", views.RegistrationHome.as_view(), name="registration_home"
    ),
    path("registration/refund/<uuid:course_pk>", views.refund, name="refund"),
    path("registration/signup/", views.CourseSignUp.as_view(), name="course_signup"),
    path("registration/cart/", views.CartView.as_view(), name="cart"),
    path("profile/", views.ProfileView.as_view(), name="profile"),
]
