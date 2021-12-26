# Generated by Django 3.2.10 on 2021-12-25 07:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("registration", "0005_registrationsettings_cancellation_fee"),
    ]

    operations = [
        migrations.AddField(
            model_name="coursebought",
            name="refund_id",
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name="coursebought",
            name="refunded",
            field=models.BooleanField(default=False),
        ),
    ]
