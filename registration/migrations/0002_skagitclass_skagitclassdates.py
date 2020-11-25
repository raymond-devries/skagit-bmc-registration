# Generated by Django 3.1.3 on 2020-11-24 05:57

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("registration", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="SkagitClass",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=200)),
                ("description", models.TextField(blank=True)),
                ("user", models.ManyToManyField(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="SkagitClassDates",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=200)),
                ("start", models.DateTimeField()),
                ("end", models.DateTimeField()),
                (
                    "skagit_class",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="registration.skagitclass",
                    ),
                ),
            ],
        ),
    ]