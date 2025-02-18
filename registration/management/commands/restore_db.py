import logging
import subprocess
import tempfile

import boto3
from django.core.management import BaseCommand, call_command
from django.db import connection, transaction

from SkagitRegistration import settings

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Command(BaseCommand):
    help = "Back up database to s3"

    def add_arguments(self, parser):
        parser.add_argument("file_name", type=str, help="db backup file name")

    def handle(self, *args, **options):
        logger.warning("Restoring DB")
        confirmed = input("This could be a destructive action, continue? (y/n)")
        if confirmed.lower() != "y":
            return
        file_name = options["file_name"]
        call_command("migrate")

        with tempfile.NamedTemporaryFile() as temp_f:
            s3_client = boto3.client("s3", settings.AWS_REGION)
            s3_client.download_fileobj(settings.DB_BACKUP_BUCKET, file_name, temp_f)

            with connection.cursor() as cursor:
                cursor.execute("TRUNCATE django_migrations")
            subprocess.run(
                ["psql", "-d", settings.DATABASE_URL, "-f", temp_f.name], check=True
            )
