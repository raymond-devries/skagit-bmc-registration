# Generated by Django 3.1.3 on 2020-11-23 00:25

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import localflavor.us.models
import phonenumber_field.modelfields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BMCRegistration',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('address', models.CharField(max_length=300)),
                ('address_2', models.CharField(blank=True, max_length=300)),
                ('city', models.CharField(max_length=100)),
                ('state', localflavor.us.models.USStateField(max_length=2)),
                ('zip_code', localflavor.us.models.USZipCodeField(max_length=10)),
                ('phone_1', phonenumber_field.modelfields.PhoneNumberField(max_length=128, region=None)),
                ('phone_2', phonenumber_field.modelfields.PhoneNumberField(blank=True, max_length=128, region=None)),
                ('date_of_birth', models.DateField()),
                ('gender', models.CharField(choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')], max_length=1)),
                ('emergency_contact_name', models.CharField(max_length=200)),
                ('emergency_contact_relationship_to_you', models.CharField(max_length=200)),
                ('emergency_contact_phone_number', phonenumber_field.modelfields.PhoneNumberField(max_length=128, region=None)),
                ('physical_fitness', models.TextField()),
                ('medical_conditions', models.BooleanField()),
                ('medical_condition_description', models.TextField(blank=True)),
                ('allergy_conditions', models.BooleanField()),
                ('allergy_condition_description', models.TextField(blank=True)),
                ('medications', models.BooleanField()),
                ('medications_descriptions', models.TextField(blank=True)),
                ('medical_insurance', models.BooleanField()),
                ('name_of_policy_holder', models.CharField(max_length=200)),
                ('relation_of_policy_holder', models.CharField(max_length=100)),
                ('signature', models.CharField(max_length=3)),
                ('todays_date', models.DateField()),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
