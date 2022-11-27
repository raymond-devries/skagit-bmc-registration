import datetime
import uuid

import stripe
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
DISCOUNT_GROUP_PREFIX = "pid__"


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class Profile(BaseModel):
    user = models.OneToOneField(User, models.CASCADE)
    email_confirmed = models.BooleanField(default=False)
    stripe_customer_id = models.CharField(max_length=200)

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

    @property
    def course_names(self):
        courses = Course.objects.filter(participants=self.user).values_list(
            "type__name", flat=True
        )
        return ", ".join(courses)


@receiver(post_save, sender=User)
def add_new_user_items(instance, created, **kwargs):
    if created:
        customer = stripe.Customer.create(
            email=instance.email, name=instance.get_full_name()
        )
        Profile.objects.create(user=instance, stripe_customer_id=customer.stripe_id)
        UserCart.objects.create(user=instance)


class RegistrationSettings(BaseModel):
    early_registration_open = models.DateTimeField()
    early_signup_code = models.CharField(max_length=15, blank=True)
    registration_open = models.DateTimeField()
    registration_close = models.DateTimeField()
    refund_period = models.DurationField(default=datetime.timedelta(days=14))
    cancellation_fee = models.PositiveIntegerField()
    time_to_pay_invoice = models.DurationField(default=datetime.timedelta(days=2))

    def save(self, *args, **kwargs):
        if not self.pk and RegistrationSettings.objects.exists():
            raise ValidationError("There can be only one RegistrationSettings instance")
        return super(RegistrationSettings, self).save(*args, **kwargs)


class EarlySignupEmail(BaseModel):
    email = models.EmailField()

    def __str__(self):
        return self.email


class RegistrationForm(BaseModel):
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


class CourseType(BaseModel):
    name = models.CharField(max_length=300)
    abbreviation = models.CharField(max_length=5)
    requirement = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True
    )
    description = models.TextField(blank=True)
    fitness_level = models.TextField(blank=True)
    visible = models.BooleanField(default=True)
    cost = models.PositiveIntegerField()

    def __str__(self):
        return self.name

    @property
    def cost_human(self):
        return human_readable_cost(self.cost)


class Course(BaseModel):
    type = models.ForeignKey(CourseType, on_delete=models.CASCADE)
    specifics = models.TextField()
    capacity = models.PositiveSmallIntegerField()
    expected_capacity = models.PositiveIntegerField()
    participants = models.ManyToManyField(User, blank=True, related_name="participants")
    instructors = models.ManyToManyField(User, blank=True, related_name="instructors")
    shown = models.BooleanField(default=True)

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

    @property
    def refund_eligble(self):
        course_dates = self.coursedate_set
        if not course_dates.exists():
            return False
        return (
            datetime.datetime.now(tz=datetime.timezone.utc)
            <= course_dates.earliest("start").start
            - RegistrationSettings.objects.first().refund_period
        )

    @property
    def spots_held_for_wait_list(self):
        return self.expected_capacity - self.capacity

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


class WaitList(BaseModel):
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


class WaitListInvoice(BaseModel):
    user = models.ForeignKey(User, models.PROTECT, null=True)
    course = models.ForeignKey(Course, models.PROTECT)
    date_added = models.DateTimeField(auto_now_add=True)
    email = models.CharField(max_length=200)
    expires = models.DateTimeField()
    invoice_id = models.CharField(max_length=200)
    paid = models.BooleanField(default=False)
    voided = models.BooleanField(default=False)


class CourseDate(BaseModel):
    course = models.ForeignKey(Course, models.CASCADE)
    name = models.CharField(max_length=200)
    start = models.DateTimeField()
    end = models.DateTimeField()

    class Meta:
        ordering = ["start", "pk"]

    def __str__(self):
        return (
            f"{self.course.type}/{self.course.specifics}/{self.name}: "
            f"{self.start.date()} - {self.end.date()}"
        )


class GearItem(BaseModel):
    type = models.ForeignKey(CourseType, models.CASCADE, null=True, blank=True)
    item = models.CharField(max_length=300)

    class Meta:
        ordering = ["item", "pk"]

    def __str__(self):
        return f"{self.type.name}/{self.item}"


class PreviousStudentDiscount(BaseModel):
    email = models.EmailField(unique=True)
    discount = models.PositiveIntegerField()


class UserCart(BaseModel):
    user = models.OneToOneField(User, models.CASCADE)

    @property
    def num_of_items(self):
        return CartItem.objects.filter(cart=self).count()

    @property
    def cost(self):
        cost_sum = self.cartitem_set.aggregate(Sum("course__type__cost"))
        cost = cost_sum["course__type__cost__sum"]
        return 0 if cost is None else cost

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


class CartItem(BaseModel):
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


class PaymentRecord(BaseModel):
    user = models.ForeignKey(User, models.PROTECT)
    checkout_session_id = models.CharField(max_length=200, blank=True)
    payment_intent_id = models.CharField(max_length=200, blank=True)
    invoice_id = models.CharField(max_length=200, blank=True)


class CourseBought(BaseModel):
    payment_record = models.ForeignKey(PaymentRecord, models.PROTECT)
    course = models.ForeignKey(Course, models.SET_NULL, null=True)
    product_id = models.CharField(max_length=200)
    price_id = models.CharField(max_length=200)
    refunded = models.BooleanField(default=False)
    refund_id = models.CharField(max_length=200, blank=True)
    coupon_id = models.CharField(max_length=200, blank=True)

    @property
    def refund_eligible(self):
        if self.refunded:
            return False
        return self.course.refund_eligble


def handle_wait_list(course: Course):
    wait_list = WaitList.objects.filter(course=course).order_by("date_added").first()
    if wait_list is not None:
        description = (
            "A spot has opened up in a course you were on the wait list for. "
            "Please pay this invoice by the due to be added to the course."
        )
        expiration = (
            datetime.datetime.now(tz=datetime.timezone.utc)
            + RegistrationSettings.objects.first().time_to_pay_invoice
        )
        stripe.InvoiceItem.create(
            customer=wait_list.user.profile.stripe_customer_id,
            amount=course.type.cost,
            currency="usd",
            description=str(course),
        )
        invoice = stripe.Invoice.create(
            customer=wait_list.user.profile.stripe_customer_id,
            collection_method="send_invoice",
            due_date=expiration,
            description=description,
            metadata={"course_id": str(course.id)},
        )
        invoice.send_invoice()
        wait_list.delete()
        WaitListInvoice.objects.create(
            user=wait_list.user,
            course=wait_list.course,
            email=wait_list.user.email,
            expires=expiration,
            invoice_id=invoice.id,
        )
        return True
    return False


def get_course_participant_values(course: Course):
    participants = course.participants
    fields = (
        "First Name",
        "Last Name",
        "Email",
        "Address 1",
        "Address 2",
        "City",
        "State",
        "Zip Code",
        "Phone 1",
        "Phone 2",
        "DOB",
        "Gender",
        "Pronouns",
        "Emergency Contact Name",
        "Emergency Contact Relationship",
        "Emergency Contact Phone Number",
        "Physical Fitness",
        "Medical Conditions",
        "Allergies",
        "Name of Policy Holder",
        "Relation of Policy Holder",
    )
    values = participants.values_list(
        "first_name",
        "last_name",
        "email",
        "registrationform__address",
        "registrationform__address_2",
        "registrationform__city",
        "registrationform__state",
        "registrationform__zip_code",
        "registrationform__phone_1",
        "registrationform__phone_2",
        "registrationform__date_of_birth",
        "registrationform__gender",
        "registrationform__pronouns",
        "registrationform__emergency_contact_name",
        "registrationform__emergency_contact_relationship_to_you",
        "registrationform__emergency_contact_phone_number",
        "registrationform__physical_fitness",
        "registrationform__medical_condition_description",
        "registrationform__allergy_condition_description",
        "registrationform__name_of_policy_holder",
        "registrationform__relation_of_policy_holder",
    )
    return fields, values
