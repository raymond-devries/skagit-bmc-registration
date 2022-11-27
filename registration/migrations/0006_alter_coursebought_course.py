# Generated by Django 4.1.2 on 2022-11-27 00:20

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "registration",
            "0003_previousstudentdiscount_squashed_0005_coursebought_coupon_id",
        ),
    ]

    operations = [
        migrations.AlterField(
            model_name="coursebought",
            name="course",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="registration.course",
            ),
        ),
    ]
