from datetime import datetime

import pytest
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from model_bakery import baker

from registration import models

pytestmark = pytest.mark.django_db


def test_registration_form___str__():
    user = baker.make(User, first_name="test", last_name="user")
    registration_form = baker.make(
        models.RegistrationForm,
        zip_code=98273,
        phone_1="+155555555555",
        emergency_contact_phone_number="+155555555555",
        user=user,
    )
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
    assert course.is_full is True


@pytest.mark.django_db(transaction=True)
def test_course_add_too_many_participants(generate_course):
    course = generate_course
    course.participants.add(baker.make(User))
    with pytest.raises(ValidationError):
        course.participants.add(baker.make(User))

    assert course.participants.count() == 9


@pytest.mark.parametrize(
    ["prices", "expected_price"],
    [
        ([5000], 5000),
        ([10000, 5000], 15000),
        ([10000, 3000, 4000, 2000], 19000),
    ],
)
def test_user_cart_price_property(prices, expected_price):
    course_types = [baker.make(models.CourseType, cost=price) for price in prices]
    courses = [
        baker.make(models.Course, type=course_type) for course_type in course_types
    ]
    cart = baker.make(models.UserCart)
    [baker.make(models.CartItem, cart=cart, course=course) for course in courses]
    assert cart.cost == expected_price
