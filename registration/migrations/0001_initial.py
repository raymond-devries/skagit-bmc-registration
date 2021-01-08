# Generated by Django 3.1.5 on 2021-01-08 23:08

import django.db.models.deletion
import localflavor.us.models
import phonenumber_field.modelfields
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Course",
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
                ("specifics", models.TextField()),
                ("capacity", models.PositiveSmallIntegerField()),
                (
                    "instructors",
                    models.ManyToManyField(
                        blank=True,
                        related_name="instructors",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "participants",
                    models.ManyToManyField(
                        blank=True,
                        related_name="participants",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="CourseType",
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
                ("name", models.CharField(max_length=300)),
                ("abbreviation", models.CharField(max_length=5)),
                ("description", models.TextField(blank=True)),
                ("visible", models.BooleanField(default=True)),
                ("cost", models.PositiveIntegerField()),
                (
                    "requirement",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="registration.coursetype",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Discount",
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
                ("number_of_courses", models.PositiveSmallIntegerField(unique=True)),
                ("discount", models.PositiveIntegerField()),
                ("stripe_id", models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name="EarlySignupEmail",
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
                ("email", models.EmailField(max_length=254)),
            ],
        ),
        migrations.CreateModel(
            name="RegistrationSettings",
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
                ("early_registration_open", models.DateTimeField()),
                ("early_signup_code", models.CharField(max_length=15)),
                ("registration_open", models.DateTimeField()),
                ("registration_close", models.DateTimeField()),
            ],
        ),
        migrations.CreateModel(
            name="UserCart",
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
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="RegistrationForm",
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
                ("address", models.CharField(max_length=300)),
                ("address_2", models.CharField(blank=True, max_length=300)),
                ("city", models.CharField(max_length=100)),
                ("state", localflavor.us.models.USStateField(max_length=2)),
                ("zip_code", localflavor.us.models.USZipCodeField(max_length=10)),
                (
                    "phone_1",
                    phonenumber_field.modelfields.PhoneNumberField(
                        max_length=128, region=None
                    ),
                ),
                (
                    "phone_2",
                    phonenumber_field.modelfields.PhoneNumberField(
                        blank=True, max_length=128, region=None
                    ),
                ),
                ("date_of_birth", models.DateField()),
                (
                    "gender",
                    models.CharField(
                        choices=[
                            ("M", "Male"),
                            ("F", "Female"),
                            ("N", "Non-Binary"),
                            ("U", "Does not wish to identify"),
                        ],
                        max_length=1,
                    ),
                ),
                ("pronouns", models.CharField(blank=True, max_length=30)),
                ("emergency_contact_name", models.CharField(max_length=200)),
                (
                    "emergency_contact_relationship_to_you",
                    models.CharField(max_length=200),
                ),
                (
                    "emergency_contact_phone_number",
                    phonenumber_field.modelfields.PhoneNumberField(
                        max_length=128, region=None
                    ),
                ),
                ("physical_fitness", models.TextField()),
                ("medical_condition_description", models.TextField(blank=True)),
                ("allergy_condition_description", models.TextField(blank=True)),
                ("medications_descriptions", models.TextField(blank=True)),
                ("medical_insurance", models.BooleanField()),
                ("name_of_policy_holder", models.CharField(max_length=200)),
                ("relation_of_policy_holder", models.CharField(max_length=100)),
                ("signature", models.CharField(max_length=3)),
                ("todays_date", models.DateField()),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Profile",
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
                ("email_confirmed", models.BooleanField(default=False)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="PaymentRecord",
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
                ("payment_id", models.CharField(max_length=100)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="GearItem",
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
                ("item", models.CharField(max_length=300)),
                (
                    "type",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="registration.coursetype",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="CourseDate",
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
                    "course",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="registration.course",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="CourseBought",
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
                (
                    "course",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="registration.course",
                    ),
                ),
                (
                    "payment_record",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="registration.paymentrecord",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="course",
            name="type",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="registration.coursetype",
            ),
        ),
        migrations.CreateModel(
            name="CartItem",
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
                (
                    "cart",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="registration.usercart",
                    ),
                ),
                (
                    "course",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="registration.course",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="WaitList",
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
                ("date_added", models.DateTimeField(auto_now_add=True)),
                (
                    "course",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="registration.course",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "unique_together": {("course", "user")},
            },
        ),
    ]
