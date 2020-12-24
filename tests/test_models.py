from datetime import datetime

import pytest
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from model_bakery import baker

from registration import models

pytestmark = pytest.mark.django_db


@pytest.fixture
def create_registration_form():
    def _create_registration_form(user):
        return baker.make(
            models.RegistrationForm,
            zip_code=98101,
            phone_1="+155555555555",
            emergency_contact_phone_number="+155555555555",
            user=user,
        )

    return _create_registration_form


def test_registration_form___str__(create_registration_form):
    user = baker.make(User, first_name="test", last_name="user")
    registration_form = create_registration_form(user)
    assert str(registration_form) == "test user registration form"


def test_course_type___str__():
    course_type = baker.make(models.CourseType, name="test course")
    assert str(course_type) == "test course"


@pytest.fixture
def generate_course():
    participants_set = baker.prepare(User, _quantity=8)
    course_type = baker.make(models.CourseType, name="test course")
    course = baker.make(
        models.Course,
        participants=participants_set,
        type=course_type,
        specifics="Class 1",
        capacity=9,
    )
    baker.make(
        models.CourseDate,
        course=course,
        start=datetime(2021, 5, 20),
        end=datetime(2021, 5, 22),
    )
    return course


def test_course___str__(generate_course):
    assert str(generate_course) == "test course/Class 1/2021-05-20 - 2021-05-22"


def test_course_is_full(generate_course):
    course = generate_course
    assert course.is_full is False
    course.participants.add(baker.make(User))
    assert course.is_full


@pytest.mark.django_db(transaction=True)
def test_course_add_too_many_participants(generate_course):
    course = generate_course
    course.participants.add(baker.make(User))
    with pytest.raises(ValidationError) as e:
        course.participants.add(baker.make(User))

    assert str(course) in str(e.value)
    assert course.participants.count() == 9


def test_delete_item_from_cart_when_course_is_full(create_registration_form):
    participants = baker.prepare(models.User, _quantity=4)
    course = baker.make(models.Course, capacity=5, participants=participants)
    user = baker.make(User)
    create_registration_form(user)
    cart = models.UserCart.objects.get(user=user)
    baker.make(models.CartItem, course=course, cart=cart)
    assert models.CartItem.objects.filter(course=course).exists()
    added_participant = baker.make(User)
    course.participants.add(added_participant)
    assert models.CartItem.objects.filter(course=course).exists() is False


@pytest.mark.parametrize(
    ["prices", "expected_price"],
    [
        ([], 0),
        ([5000], 5000),
        ([10000, 5000], 15000),
        ([10000, 3000, 4000, 2000], 19000),
    ],
)
def test_user_cart_price_property(prices, expected_price, create_registration_form):
    course_types = [baker.make(models.CourseType, cost=price) for price in prices]
    courses = [
        baker.make(models.Course, type=course_type) for course_type in course_types
    ]
    user = baker.make(User)
    create_registration_form(user)
    cart = models.UserCart.objects.get(user=user)
    [baker.make(models.CartItem, cart=cart, course=course) for course in courses]
    assert cart.cost == expected_price


def test_automatic_new_user_cart_creation():
    user = baker.make(User)
    assert models.UserCart.objects.filter(user=user).exists()


def test_add_full_course_to_cart():
    participants = baker.prepare(models.User, _quantity=5)
    course = baker.make(models.Course, capacity=5, participants=participants)
    user = baker.make(User)
    cart = models.UserCart.objects.get(user=user)
    with pytest.raises(ValidationError) as e:
        models.CartItem.objects.create(cart=cart, course=course)
    assert str(course) in str(e.value)


def test_add_item_to_cart_registration_form_validation(create_registration_form):
    user = baker.make(User)
    cart = models.UserCart.objects.get(user=user)
    with pytest.raises(ValidationError):
        baker.make(models.CartItem, cart=cart)
    assert models.CartItem.objects.filter(cart=cart).exists() is False

    create_registration_form(user)
    baker.make(models.CartItem, cart=cart)
    assert models.CartItem.objects.filter(cart=cart).exists()


@pytest.fixture
def course_pre_req_setup(create_registration_form):
    user = baker.make(User)
    cart = models.UserCart.objects.get(user=user)
    create_registration_form(user)

    pre_req_course_type = baker.make(models.CourseType)
    course_type = baker.make(models.CourseType, requirement=pre_req_course_type)
    pre_req_course = baker.make(models.Course, type=pre_req_course_type)
    course = baker.make(models.Course, type=course_type)

    return cart, pre_req_course, course


def test_verify_course_requirements(course_pre_req_setup):
    cart, pre_req_course, course = course_pre_req_setup

    with pytest.raises(ValidationError) as e:
        baker.make(models.CartItem, cart=cart, course=course)
    assert pre_req_course.type.name in str(e.value)


def test_verify_course_requirement_requirement_in_cart(course_pre_req_setup):
    cart, pre_req_course, course = course_pre_req_setup

    # Add appropriate pre_req course and then add course.
    # If it doesn't raise an error test is successful
    baker.make(models.CartItem, cart=cart, course=pre_req_course)
    baker.make(models.CartItem, cart=cart, course=course)


def test_verify_course_requirement_user_signed_up_for_requirement(course_pre_req_setup):
    cart, pre_req_course, course = course_pre_req_setup

    # Add user to participants of a pre_req course and then add course.
    # If it doesn't raise an error test is successful
    pre_req_course.participants.add(cart.user)
    baker.make(models.CartItem, cart=cart, course=course)