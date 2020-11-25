from django.contrib.auth.models import User
from django.db import models
from localflavor.us import models as us_model
from phonenumber_field.modelfields import PhoneNumberField

GENDER_CHOICES = [("M", "Male"), ("F", "Female"), ("O", "Other")]


class RegistrationForm(models.Model):
    user = models.OneToOneField(User, models.CASCADE)
    address = models.CharField(max_length=300)
    address_2 = models.CharField(max_length=300, blank=True)
    city = models.CharField(max_length=100)
    state = us_model.USStateField()
    zip_code = us_model.USZipCodeField()
    phone_1 = PhoneNumberField()
    phone_2 = PhoneNumberField(blank=True)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    emergency_contact_name = models.CharField(max_length=200)
    emergency_contact_relationship_to_you = models.CharField(max_length=200)
    emergency_contact_phone_number = PhoneNumberField()
    physical_fitness = models.TextField()
    medical_conditions = models.BooleanField()
    medical_condition_description = models.TextField(blank=True)
    allergy_conditions = models.BooleanField()
    allergy_condition_description = models.TextField(blank=True)
    medications = models.BooleanField()
    medications_descriptions = models.TextField(blank=True)
    medical_insurance = models.BooleanField()
    name_of_policy_holder = models.CharField(max_length=200)
    relation_of_policy_holder = models.CharField(max_length=100)
    signature = models.CharField(max_length=3)
    todays_date = models.DateField()


class SkagitClass(models.Model):
    user = models.ManyToManyField(User)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)


class SkagitClassDates(models.Model):
    skagit_class = models.ForeignKey(SkagitClass, models.CASCADE)
    name = models.CharField(max_length=200)
    start = models.DateTimeField()
    end = models.DateTimeField()
