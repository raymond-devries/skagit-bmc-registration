from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum
from django.db.models.signals import m2m_changed, post_save, pre_save
from django.dispatch import receiver
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


class CourseType(models.Model):
    name = models.CharField(max_length=300)
    requirement = models.ForeignKey(
        "self", on_delete=models.PROTECT, null=True, blank=True
    )
    description = models.TextField(blank=True)
    visible = models.BooleanField(default=True)
    cost = models.PositiveIntegerField()

    def __str__(self):
        return self.name


class Course(models.Model):
    type = models.ForeignKey(CourseType, on_delete=models.CASCADE)
    specifics = models.TextField()
    capacity = models.PositiveSmallIntegerField()
    participants = models.ManyToManyField(User, blank=True, related_name="participants")
    wait_list = models.ManyToManyField(User, blank=True, related_name="wait_list")
    instructors = models.ManyToManyField(User, blank=True, related_name="instructors")

    @property
    def is_full(self):
        return self.participants.count() == self.capacity

    def __str__(self):
        dates = CourseDate.objects.filter(course=self)
        if dates.exists():
            start = dates.earliest("start").start.date()
            end = dates.latest("end").end.date()
        else:
            start = None
            end = None
        return f"{self.type}/{self.specifics}/{start} - {end}"


def added_participant(action, instance, **kwargs):
    if action == "pre_add":
        if instance.participants.count() >= instance.capacity:
            raise ValidationError(
                f"There is already too many participants in {instance}, "
                f"an additional participant cannot be added"
            )

    if action == "post_add":
        if instance.is_full:
            CartItem.objects.filter(course=instance).delete()


m2m_changed.connect(added_participant, sender=Course.participants.through)


class CourseDate(models.Model):
    course = models.ForeignKey(Course, models.CASCADE)
    name = models.CharField(max_length=200)
    start = models.DateTimeField()
    end = models.DateTimeField()

    def __str__(self):
        return (
            f"{self.course.type}/{self.course.specifics}/{self.name}: "
            f"{self.start.date()} - {self.end.date()}"
        )


class Discount(models.Model):
    number_of_courses = models.PositiveSmallIntegerField()
    discount = models.PositiveIntegerField()


class UserCart(models.Model):
    user = models.OneToOneField(User, models.CASCADE)

    @property
    def cost(self):
        cost_sum = CartItem.objects.filter(cart=self).aggregate(
            Sum("course__type__cost")
        )
        cost = cost_sum["course__type__cost__sum"]
        return 0 if cost is None else cost


@receiver(post_save, sender=User)
def add_new_user_cart(instance, created, **kwargs):
    if created:
        UserCart.objects.create(user=instance)


class CartItem(models.Model):
    cart = models.ForeignKey(UserCart, models.CASCADE)
    course = models.ForeignKey(Course, models.CASCADE)


@receiver(pre_save, sender=CartItem)
def add_full_course_to_cart(instance, **kwargs):
    if instance.course.is_full:
        raise ValidationError(
            f"A cart item cannot be created with course: {instance.course}, it is full"
        )


class PaymentRecord(models.Model):
    user = models.ForeignKey(User, models.PROTECT)
    payment_id = models.CharField(max_length=100)


class CourseBought(models.Model):
    payment_record = models.ForeignKey(PaymentRecord, models.CASCADE)
    course = models.ForeignKey(Course, models.PROTECT)
