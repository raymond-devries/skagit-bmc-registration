from django.apps import AppConfig


class RegistrationConfig(AppConfig):
    name = "registration"

    def ready(self):
        from django.contrib.auth.models import Group

        Group.objects.get_or_create(name="instructor")
