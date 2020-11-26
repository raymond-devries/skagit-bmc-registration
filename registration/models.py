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

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} " f"registration form"


class ClassType(models.Model):
    name = models.CharField(max_length=300)
    requirement = models.ForeignKey(
        "self", on_delete=models.PROTECT, null=True, blank=True
    )
    description = models.TextField(blank=True)
    visible = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class SkagitClass(models.Model):
    class Meta:
        verbose_name_plural = "Skagit classes"

    type = models.ForeignKey(ClassType, on_delete=models.CASCADE)
    specifics = models.TextField()
    capacity = models.PositiveSmallIntegerField()
    participants = models.ManyToManyField(User, blank=True, related_name="participants")
    wait_list = models.ManyToManyField(User, blank=True, related_name="wait_list")
    instructors = models.ManyToManyField(User, blank=True, related_name="instructors")

    def __str__(self):
        dates = SkagitClassDate.objects.filter(skagit_class=self)
        if dates.exists():
            start = dates.earliest("start").start.date()
            end = dates.latest("end").end.date()
        else:
            start = None
            end = None
        return f"{self.type}/{self.specifics}/{start} - {end}"


class SkagitClassDate(models.Model):
    skagit_class = models.ForeignKey(SkagitClass, models.CASCADE)
    name = models.CharField(max_length=200)
    start = models.DateTimeField()
    end = models.DateTimeField()

    def __str__(self):
        return (
            f"{self.skagit_class.type}/{self.skagit_class.specifics}/{self.name}: "
            f"{self.start.date()} - {self.end.date()}"
        )
