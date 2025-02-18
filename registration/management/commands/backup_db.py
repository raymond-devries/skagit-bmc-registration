import logging
import subprocess
from datetime import datetime, timezone

import boto3
from django.core.management import BaseCommand

from SkagitRegistration import settings

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Command(BaseCommand):
    help = "Back up database to s3"

    @staticmethod
    def delete_all_but_recent_files(bucket_name, keep_count=10):
        # Create an S3 client
        s3_client = boto3.client("s3")

        # List all objects in the bucket
        response = s3_client.list_objects_v2(Bucket=bucket_name)

        # Check if the bucket has any objects
        if "Contents" not in response:
            logger.info(f"No files found in bucket: {bucket_name}")
            return

        # Extract the list of objects and sort them by LastModified date (newest first)
        objects = response["Contents"]
        sorted_objects = sorted(objects, key=lambda x: x["LastModified"], reverse=True)

        # Separate the files to keep and the files to delete
        files_to_keep = sorted_objects[:keep_count]
        files_to_delete = sorted_objects[keep_count:]

        # logger.info the files to keep
        logger.info("Files to keep:")
        for obj in files_to_keep:
            logger.info(f"- {obj['Key']} (Last Modified: {obj['LastModified']})")

        # Delete the files that are not in the top 10 most recent
        if files_to_delete:
            logger.info("\nFiles to delete:")
            delete_keys = [{"Key": obj["Key"]} for obj in files_to_delete]
            for obj in files_to_delete:
                logger.info(f"- {obj['Key']} (Last Modified: {obj['LastModified']})")

            # Perform the deletion
            s3_client.delete_objects(
                Bucket=bucket_name, Delete={"Objects": delete_keys}
            )
            logger.info(f"\nDeleted {len(files_to_delete)} files.")
        else:
            logger.info("\nNo files to delete.")

    def handle(self, *args, **options):
        logger.info("Backing up database")
        s3_client = boto3.resource("s3", settings.AWS_REGION)
        try:
            backup = subprocess.run(
                [
                    "pg_dump",
                    "--data-only",
                    "--schema",
                    "public",
                    "--exclude-table",
                    "django_content_type",
                    "--exclude-table",
                    "auth_permission",
                    "--exclude-table",
                    "django_session",
                    settings.DATABASE_URL,
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            now = datetime.now(timezone.utc)
            timestamp = int(now.timestamp())
            s3_client.Object(
                settings.DB_BACKUP_BUCKET,
                f"{timestamp}_{now.date().isoformat()}_backup.sql",
            ).put(Body=backup.stdout)

            self.delete_all_but_recent_files(settings.DB_BACKUP_BUCKET)
        except subprocess.CalledProcessError as e:
            logger.error("Failed to backup database")
