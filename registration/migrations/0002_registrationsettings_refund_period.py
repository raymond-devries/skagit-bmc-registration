# Generated by Django 3.2.9 on 2021-12-24 22:09

import datetime

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("registration", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="registrationsettings",
            name="refund_period",
            field=models.DurationField(default=datetime.timedelta(days=14)),
        ),
    ]