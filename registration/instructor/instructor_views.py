from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.models import User
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
