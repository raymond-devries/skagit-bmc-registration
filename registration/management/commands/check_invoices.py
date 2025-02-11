import logging
from datetime import datetime, timezone

import stripe
from django.core.management.base import BaseCommand

from registration import models


class Command(BaseCommand):
    help = "Checks stripe invoices and removes expired ones"

    def handle(self, *args, **options):
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        wait_list_invoices = models.WaitListInvoice.objects.filter(
            expires__lte=datetime.now(tz=timezone.utc), paid=False, voided=False
        )
        logger.info(f"{len(wait_list_invoices)} expired wait list invoices found")

        for invoice in wait_list_invoices:
            logger.info(f"Voiding invoice {invoice.invoice_id}")
            stripe.Invoice.void_invoice(invoice.invoice_id)
            invoice.voided = True
            invoice.save()
            course = invoice.course
            created = models.handle_wait_list(course)
            if created:
                logger.info(
                    f"Created new invoice {created.invoice_id} for {invoice.user.email}"
                )
            else:
                logger.info("No new invoices were created")
                course.capacity += 1
                course.save()
