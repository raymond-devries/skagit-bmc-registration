from django.apps import AppConfig


class RegistrationConfig(AppConfig):
    name = "registration"

    def ready(self):
        from django.contrib.auth.models import Group

        from registration.models import INSTRUCTOR_GROUP

        Group.objects.get_or_create(INSTRUCTOR_GROUP)
