from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

from registration import models


class CurrentRegistrationsView(UserPassesTestMixin, TemplateView):
    template_name = "bmc_registration/instructor/current_registrations.html"

    def test_func(self):
        return self.request.user.profile.is_instructor

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["registered_users"] = (
            User.objects.filter(
                participants__in=models.Course.objects.filter(type__visible=True)
            )
            .distinct()
            .order_by("first_name", "last_name")
        )
        context["course_types"] = models.CourseType.objects.filter(visible=True)
        return context


class RegistrantView(UserPassesTestMixin, TemplateView):
    template_name = "bmc_registration/instructor/registrant_view.html"

    def test_func(self):
        return self.request.user.profile.is_instructor

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        registrant = get_object_or_404(User, username=self.kwargs["username"])
        context["registrant"] = registrant
        context["courses"] = models.Course.objects.filter(participants=registrant)
        context["wait_list_courses"] = models.Course.objects.filter(
            waitlist__user=registrant
        )
        context["registration_form"] = models.RegistrationForm(user=registrant)
        return context
