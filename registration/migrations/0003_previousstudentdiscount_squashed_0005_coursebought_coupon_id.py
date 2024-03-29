# Generated by Django 3.2.10 on 2022-01-09 06:21

import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    replaces = [
        ("registration", "0003_previousstudentdiscount"),
        ("registration", "0004_delete_discount"),
        ("registration", "0005_coursebought_coupon_id"),
    ]

    dependencies = [
        ("registration", "0002_auto_20220103_0643"),
    ]

    operations = [
        migrations.CreateModel(
            name="PreviousStudentDiscount",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("email", models.EmailField(max_length=254, unique=True)),
                ("discount", models.PositiveIntegerField()),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.DeleteModel(
            name="Discount",
        ),
        migrations.AddField(
            model_name="coursebought",
            name="coupon_id",
            field=models.CharField(blank=True, max_length=200),
        ),
    ]
