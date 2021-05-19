from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Case, Max, Min, Q, Sum, Value, When
from django.db.models.signals import m2m_changed, post_save, pre_delete, pre_save
from django.dispatch import receiver
from django.utils import timezone
from localflavor.us import models as us_model
from phonenumber_field.modelfields import PhoneNumberField

GENDER_CHOICES = [
    ("M", "Male"),
    ("F", "Female"),
    ("N", "Non-Binary"),
    ("U", "Does not wish to identify"),
]

INSTRUCTOR_GROUP = "instructor"


class Profile(models.Model):
    user = models.OneToOneField(User, models.CASCADE)
    email_confirmed = models.BooleanField(default=False)

    @property
    def is_eligible_for_early_registration(self):
        return EarlySignupEmail.objects.filter(email__iexact=self.user.email).exists()

    @property
    def is_eligible_for_registration(self):
        registration_settings = RegistrationSettings.objects.first()
        after_early_sign_up = (
            timezone.now() > registration_settings.early_registration_open
        )
        after_sign_up = timezone.now() > registration_settings.registration_open
        before_close = timezone.now() < registration_settings.registration_close

        if (
            self.is_eligible_for_early_registration
            and after_early_sign_up
            and before_close
        ):
            return True
        elif after_sign_up and before_close:
            return True
        return False

    @property
    def is_instructor(self):
        return self.user.groups.filter(name=INSTRUCTOR_GROUP).exists()


@receiver(post_save, sender=User)
def add_new_user_items(instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
        UserCart.objects.create(user=instance)


class RegistrationSettings(models.Model):
    early_registration_open = models.DateTimeField()
    early_signup_code = models.CharField(max_length=15, blank=True)
    registration_open = models.DateTimeField()
    registration_close = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.pk and RegistrationSettings.objects.exists():
            raise ValidationError("There can be only one RegistrationSettings instance")
        return super(RegistrationSettings, self).save(*args, **kwargs)


class EarlySignupEmail(models.Model):
    email = models.EmailField()

    def __str__(self):
        return self.email


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
    pronouns = models.CharField(max_length=30, blank=True)
    emergency_contact_name = models.CharField(max_length=200)
    emergency_contact_relationship_to_you = models.CharField(max_length=200)
    emergency_contact_phone_number = PhoneNumberField()
    physical_fitness = models.TextField()
    medical_condition_description = models.TextField(blank=True)
    allergy_condition_description = models.TextField(blank=True)
    medications_descriptions = models.TextField(blank=True)
    medical_insurance = models.BooleanField()
    name_of_policy_holder = models.CharField(max_length=200)
    relation_of_policy_holder = models.CharField(max_length=100)
    signature = models.CharField(max_length=3)
    todays_date = models.DateField()

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} " f"registration form"


def human_readable_cost(value):
    return f"${value/100 :,.2f}"


class CourseType(models.Model):
    name = models.CharField(max_length=300)
    abbreviation = models.CharField(max_length=5)
    requirement = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True
    )
    description = models.TextField(blank=True)
    visible = models.BooleanField(default=True)
    cost = models.PositiveIntegerField()

    def __str__(self):
        return self.name

    @property
    def cost_human(self):
        return human_readable_cost(self.cost)


class Course(models.Model):
    type = models.ForeignKey(CourseType, on_delete=models.CASCADE)
    specifics = models.TextField()
    capacity = models.PositiveSmallIntegerField()
    participants = models.ManyToManyField(User, blank=True, related_name="participants")
    instructors = models.ManyToManyField(User, blank=True, related_name="instructors")

    @property
    def num_of_participants(self):
        return self.participants.count()

    @property
    def is_full(self):
        return self.num_of_participants >= self.capacity

    @property
    def spots_left(self):
        return self.capacity - self.num_of_participants

    @property
    def num_on_wait_list(self):
        return WaitList.objects.filter(course=self).count()

    @property
    def start_end_date(self):
        return self.coursedate_set.aggregate(Min("start"), Max("end"))

    def user_on_wait_list(self, user):
        try:
            return WaitList.objects.get(course=self, user=user)
        except WaitList.DoesNotExist:
            return None

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


class WaitList(models.Model):
    date_added = models.DateTimeField(auto_now_add=True)
    course = models.ForeignKey(Course, models.CASCADE)
    user = models.ForeignKey(User, models.CASCADE)

    class Meta:
        unique_together = ("course", "user")

    @property
    def wait_list_place(self):
        return WaitList.objects.filter(
            date_added__lte=self.date_added, course=self.course
        ).count()


@receiver(pre_save, sender=WaitList)
def only_allow_wait_list_after_course_is_full(instance, **kwargs):
    if not instance.course.is_full:
        raise ValidationError(
            "The user cannot be added to the wait list since the"
            f"course ({instance.course}) is not full"
        )


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


class GearItem(models.Model):
    type = models.ForeignKey(CourseType, models.CASCADE, null=True, blank=True)
    item = models.CharField(max_length=300)


class Discount(models.Model):
    number_of_courses = models.PositiveSmallIntegerField(unique=True)
    discount = models.PositiveIntegerField()
    stripe_id = models.CharField(max_length=50)

    @property
    def discount_human(self):
        return human_readable_cost(self.discount)


class UserCart(models.Model):
    user = models.OneToOneField(User, models.CASCADE)

    @property
    def num_of_items(self):
        return CartItem.objects.filter(cart=self).count()

    @property
    def discount(self):
        try:
            discount = Discount.objects.get(number_of_courses=self.num_of_items)
            return discount
        except Discount.DoesNotExist:
            return None

    @property
    def cost(self):
        cost_sum = self.cartitem_set.aggregate(Sum("course__type__cost"))
        cost = cost_sum["course__type__cost__sum"]
        if (discount := self.discount) is None:
            discount = 0
        else:
            discount = discount.discount
        return 0 if cost is None else cost - discount

    @property
    def eligible_courses(self):
        course_types_in_cart_or_signed_up_for = CourseType.objects.filter(
            Q(course__cartitem__cart=self) | Q(course__participants=self.user)
        )
        # eligible courses to add to their cart include:
        # 1. Course types with no prerequisites
        # 2. Course types with prerequisites that the user has in their cart
        # 3. Course types with prerequisites that the user has registered for
        # 4. Course types that they do not already have in their cart
        # 5. Course types they have not already registered for
        #     - This in practice allows a user to only signup for course types once
        courses = (
            CourseType.objects.all()
            .order_by("name")
            .annotate(
                eligible=Case(
                    When(
                        (
                            Q(requirement=None)
                            | Q(requirement__in=course_types_in_cart_or_signed_up_for)
                        )
                        & ~Q(id__in=course_types_in_cart_or_signed_up_for),
                        then=Value(True),
                    ),
                    default=Value(False),
                    output_field=models.BooleanField(),
                )
            )
        )
        return courses


class CartItem(models.Model):
    cart = models.ForeignKey(UserCart, models.CASCADE)
    course = models.ForeignKey(Course, models.CASCADE)


@receiver(pre_save, sender=CartItem)
def cart_item_validation(instance, **kwargs):
    if instance.course.is_full:
        raise ValidationError(
            f"A cart item cannot be created with course: {instance.course}, it is full"
        )

    if not RegistrationForm.objects.filter(user=instance.cart.user).exists():
        raise ValidationError(
            "A cart item cannot be added until the user fills out a registration form"
        )

    course_types_in_cart_or_signed_up_for = CourseType.objects.filter(
        Q(course__cartitem__cart=instance.cart)
        | Q(course__participants=instance.cart.user)
    )

    if instance.course.type in course_types_in_cart_or_signed_up_for:
        raise ValidationError(
            "A cart item cannot be added with this course type since the user already "
            "has this course type in their cart or they are already signed up for"
            f"this course type ({instance.course.type})"
        )


@receiver(pre_save, sender=CartItem)
def verify_requirements(instance, **kwargs):
    requirement = instance.course.type.requirement
    if requirement is None:
        return

    user_registered_for_requirement = CourseType.objects.filter(
        course__participants=instance.cart.user
    ).exists()
    requirement_in_cart = instance.cart.cartitem_set.filter(
        course__type=requirement
    ).exists()

    if not requirement_in_cart and not user_registered_for_requirement:
        raise ValidationError(
            f"The user does not have the pre_requisite course ({requirement.name}) "
            f"in their cart or they are not registered for the course",
            requirement,
        )


@receiver(pre_delete, sender=CartItem)
def verify_requirements_before_delete(instance, **kwargs):
    cart_items_with_instance_as_requirement = instance.cart.cartitem_set.filter(
        course__type__requirement=instance.course.type
    )

    cart_items_with_instance_as_requirement.delete()


class PaymentRecord(models.Model):
    user = models.ForeignKey(User, models.PROTECT)
    payment_id = models.CharField(max_length=100)


class CourseBought(models.Model):
    payment_record = models.ForeignKey(PaymentRecord, models.PROTECT)
    course = models.ForeignKey(Course, models.PROTECT)
