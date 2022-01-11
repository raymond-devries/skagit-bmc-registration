import csv

from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

from registration import models


def instructor_check(user: User):
    return user.profile.is_instructor


class CurrentRegistrationsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = "bmc_registration/instructor/current_registrations.html"

    def test_func(self):
        return instructor_check(self.request.user)

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


class RegistrantView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = "bmc_registration/instructor/registrant_view.html"

    def test_func(self):
        return instructor_check(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        registrant = get_object_or_404(User, username=self.kwargs["username"])
        context["registrant"] = registrant
        context["courses"] = models.Course.objects.filter(participants=registrant)
        context["wait_list_items"] = models.WaitList.objects.filter(user=registrant)
        context["registration_form"] = get_object_or_404(
            models.RegistrationForm, user=registrant
        )
        return context


@user_passes_test(instructor_check)
def participant_csv(request, course_pk):
    course = models.Course.objects.get(pk=course_pk)
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{course.specifics}.csv"'
    fields, values = models.get_course_participant_values(course)

    writer = csv.writer(response)
    writer.writerow(fields)
    for value in values:
        writer.writerow(value)

    return response
