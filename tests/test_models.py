from datetime import datetime, timezone

import pytest
from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from model_bakery import baker

from registration import models
from registration.models import Course

pytestmark = pytest.mark.django_db


def test_is_eligible_for_early_registration():
    user = baker.make(User, email="user@test.com")
    assert not user.profile.is_eligible_for_early_registration
    baker.make(models.EarlySignupEmail, email=user.email)
    assert user.profile.is_eligible_for_early_registration


@pytest.mark.parametrize(
    ["date", "normal", "early_signup"],
    (
        ("2021-01-05", False, False),
        ("2021-01-12", False, True),
        ("2021-1-17", True, True),
        ("2021-2-16", False, False),
    ),
)
def test_is_eligible_for_registration(freezer, date, normal, early_signup):
    user1 = baker.make(User, email="user1@gmail.com")
    user2 = baker.make(User, email="user2@gmail.com")
    baker.make(models.EarlySignupEmail, email=user2.email)
    baker.make(
        models.RegistrationSettings,
        early_registration_open=datetime(2021, 1, 10),
        registration_open=datetime(2021, 1, 15),
        registration_close=datetime(2021, 2, 15),
    )
    freezer.move_to(date)
    assert user1.profile.is_eligible_for_registration is normal
    assert user2.profile.is_eligible_for_registration is early_signup


def test_is_instructor():
    user = baker.make(User)
    assert not user.profile.is_instructor
    group = baker.make(Group, name=models.INSTRUCTOR_GROUP)
    user.groups.add(group)
    assert user.profile.is_instructor


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


def test_course_num_of_participants_and_spots_left():
    participants_set = baker.prepare(User, _quantity=6)
    course = baker.make(models.Course, capacity=10, participants=participants_set)
    assert course.num_of_participants == 6
    assert course.spots_left == 4


def test_course_is_full(generate_course):
    course = generate_course
    assert course.is_full is False
    course.participants.add(baker.make(User))
    assert course.is_full


def test_course_wait_list():
    course = baker.make(models.Course, capacity=0)
    baker.make(models.WaitList, course=course, _quantity=20)
    assert course.num_on_wait_list == 20


def test_start_end_date():
    course = baker.make(models.Course)
    date1 = baker.make(
        models.CourseDate,
        course=course,
        start=datetime(2021, 2, 1, tzinfo=timezone.utc),
        end=datetime(2021, 2, 4, tzinfo=timezone.utc),
    )
    date2 = baker.make(
        models.CourseDate,
        course=course,
        start=datetime(2021, 2, 3, tzinfo=timezone.utc),
        end=datetime(2021, 2, 5, tzinfo=timezone.utc),
    )
    assert course.start_end_date["start__min"] == date1.start
    assert course.start_end_date["end__max"] == date2.end


def test_course_spots_held_for_wait_list():
    course = baker.make(models.Course, capacity=8, expected_capacity=10)
    assert course.spots_held_for_wait_list == 2


def test_user_on_wait_list():
    course = baker.make(models.Course, capacity=0)
    user = baker.make(User)
    assert course.user_on_wait_list(user) is None
    wait_list = baker.make(models.WaitList, course=course, user=user)
    assert course.user_on_wait_list(user).id == wait_list.id


@pytest.mark.django_db(transaction=True)
def test_course_add_too_many_participants(generate_course):
    course = generate_course
    course.participants.add(baker.make(User))
    with pytest.raises(ValidationError) as e:
        course.participants.add(baker.make(User))

    assert str(course) in str(e.value)
    assert course.participants.count() == 9


def test_only_allow_wait_list_after_course_is_full():
    course = baker.make(models.Course, capacity=1)
    with pytest.raises(ValidationError):
        baker.make(models.WaitList, course=course)
    course.participants.add(baker.make(User))
    baker.make(models.WaitList, course=course)


def test_wait_list_place():
    course = baker.make(models.Course, capacity=0)
    course2 = baker.make(models.Course, capacity=0)
    baker.make(models.WaitList, course=course2)
    wait_list_item1 = baker.make(models.WaitList, course=course)
    wait_list_item2 = baker.make(models.WaitList, course=course)
    assert wait_list_item1.wait_list_place == 1
    assert wait_list_item2.wait_list_place == 2


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


def test_cart_num_of_items(create_registration_form):
    user = baker.make(User)
    create_registration_form(user)
    cart = models.UserCart.objects.get(user=user)
    baker.make(models.CartItem, cart=cart, _quantity=5)
    assert cart.num_of_items == 5


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


def test_automatic_new_user_item_creation():
    user = baker.make(User)
    assert models.UserCart.objects.filter(user=user).exists()
    assert models.Profile.objects.filter(user=user).exists()


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


def test_add_item_to_cart_duplicate_course_type_sign_up(create_registration_form):
    user = baker.make(User)
    cart = models.UserCart.objects.get(user=user)
    create_registration_form(user)

    course_type = baker.make(models.CourseType)
    course1 = baker.make(models.Course, type=course_type)
    course2 = baker.make(models.Course, type=course_type)

    cart_item1 = baker.make(models.CartItem, cart=cart, course=course1)
    with pytest.raises(ValidationError):
        baker.make(models.CartItem, cart=cart, course=course2)

    cart_item1.delete()
    course1.participants.add(user)
    with pytest.raises(ValidationError):
        baker.make(models.CartItem, cart=cart, course=course1)
    with pytest.raises(ValidationError):
        baker.make(models.CartItem, cart=cart, course=course2)


@pytest.fixture
def course_pre_req_setup(create_registration_form):
    user = baker.make(User, id=40)
    cart = models.UserCart.objects.get(user=user)
    create_registration_form(user)

    pre_req_course_type = baker.make(models.CourseType, id=10)
    course_type = baker.make(models.CourseType, requirement=pre_req_course_type, id=20)
    pre_req_course = baker.make(models.Course, type=pre_req_course_type, id=30)
    course = baker.make(models.Course, type=course_type, id=40)

    return cart, pre_req_course, course


@pytest.mark.django_db(transaction=True)
def test_cart_eligible_courses(course_pre_req_setup):
    cart, pre_req_course, course = course_pre_req_setup

    assert cart.eligible_courses.filter(
        eligible=True, id=pre_req_course.type.id
    ).exists()
    assert cart.eligible_courses.filter(eligible=False, id=course.type.id).exists()

    pre_req_cart_item = baker.make(models.CartItem, cart=cart, course=pre_req_course)
    assert cart.eligible_courses.filter(
        eligible=False, id=pre_req_course.type.id
    ).exists()
    assert cart.eligible_courses.filter(eligible=True, id=course.type.id).exists()

    pre_req_cart_item.delete()
    pre_req_course.participants.add(cart.user)
    assert cart.eligible_courses.filter(
        eligible=False, id=pre_req_course.type.id
    ).exists()
    assert cart.eligible_courses.filter(eligible=True, id=course.type.id).exists()

    course_cart_item = baker.make(models.CartItem, cart=cart, course=course)
    assert cart.eligible_courses.filter(
        eligible=False, id=pre_req_course.type.id
    ).exists()
    assert cart.eligible_courses.filter(eligible=False, id=course.type.id).exists()

    course_cart_item.delete()
    course.participants.add(cart.user)
    assert cart.eligible_courses.filter(
        eligible=False, id=pre_req_course.type.id
    ).exists()
    assert cart.eligible_courses.filter(eligible=False, id=course.type.id).exists()


def test_verify_course_requirements(course_pre_req_setup):
    cart, pre_req_course, course = course_pre_req_setup

    with pytest.raises(ValidationError) as e:
        baker.make(models.CartItem, cart=cart, course=course)
    assert pre_req_course.type.name in str(e.value)
    assert pre_req_course.type is e.value.args[1]


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


@pytest.mark.django_db(transaction=True)
def test_verify_course_requirement_delete_when_not_in_cart_or_signed_up(
    course_pre_req_setup,
):
    cart, pre_req_course, course = course_pre_req_setup

    cart_item_added = baker.make(models.CartItem, cart=cart, course=pre_req_course)
    baker.make(models.CartItem, cart=cart, course=course)

    cart_item_added.delete()

    assert not cart.cartitem_set.exists()


def test_course_bought_refund_eligible(freezer, registration_settings):
    course_bought = baker.make(models.CourseBought, course=baker.make(Course))
    assert not course_bought.refund_eligible
    baker.make(
        models.CourseDate,
        start=datetime(year=2022, month=3, day=20),
        course=course_bought.course,
    )
    freezer.move_to("2022-02-01")
    assert course_bought.refund_eligible
    freezer.move_to("2022-03-15")
    assert not course_bought.refund_eligible
    freezer.move_to("2022-02-01")
    course_bought.refunded = True
    course_bought.save()
    assert not course_bought.refund_eligible
