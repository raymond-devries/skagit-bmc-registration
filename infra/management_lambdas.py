import logging
import os

from django.core import management


def management_command(event, context):
    import django

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SkagitRegistration.settings")
    django.setup()
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    command = event["command"]
    logger.info(f"Calling python manage.py {command}")
    management.call_command(command)
