from django.core.management.base import BaseCommand

from registration.utils import check_invoices


class Command(BaseCommand):
    help = "Checks stripe invoices and removes expired ones"

    def handle(self, *args, **options):
        check_invoices()
