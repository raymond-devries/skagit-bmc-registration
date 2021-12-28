from datetime import datetime, timezone

import stripe
from django.core.management.base import BaseCommand

from registration import models


class Command(BaseCommand):
    help = "Checks stripe invoices and removes expired ones"

    def handle(self, *args, **options):
        wait_list_invoices = models.WaitListInvoice.objects.filter(
            expires__lte=datetime.now(tz=timezone.utc), paid=False, voided=False
        )
        for invoice in wait_list_invoices:
            stripe.Invoice.void_invoice(invoice.invoice_id)
            invoice.voided = True
            invoice.save()
            course = invoice.course
            created = models.handle_wait_list(course)
            if not created:
                course.capacity += 1
                course.save()
