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


def test_user_on_wait_list():
    course = baker.make(models.Course, capacity=0)
    user = baker.make(User)
    assert course.user_on_wait_list(user) is None
    wait_list = baker.make(models.WaitList, course=course, user=user, id=45)
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


def test_cart_discount(create_registration_form):
    user = baker.make(User)
    create_registration_form(user)
    cart = models.UserCart.objects.get(user=user)
    baker.make(models.CartItem, cart=cart, _quantity=2)
    discount = baker.make(models.Discount, number_of_courses=2, discount=500)
    assert cart.discount == discount
    baker.make(models.CartItem, cart=cart)
    assert cart.discount is None


@pytest.mark.parametrize(
    ["prices", "expected_price"],
    [
        ([], 0),
        ([5000], 5000),
        ([10000, 5000], 14500),
        ([10000, 3000, 4000, 2000], 19000),
    ],
)
def test_user_cart_price_property(prices, expected_price, create_registration_form):
    baker.make(models.Discount, number_of_courses=2, discount=500)
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

    assert pre_req_course.type in cart.eligible_courses.filter(eligible=True)
    assert course.type in cart.eligible_courses.filter(eligible=False)

    pre_req_cart_item = baker.make(models.CartItem, cart=cart, course=pre_req_course)
    assert pre_req_course.type in cart.eligible_courses.filter(eligible=False)
    assert course.type in cart.eligible_courses.filter(eligible=True)

    pre_req_cart_item.delete()
    pre_req_course.participants.add(cart.user)
    assert pre_req_course.type in cart.eligible_courses.filter(eligible=False)
    assert course.type in cart.eligible_courses.filter(eligible=True)

    course_cart_item = baker.make(models.CartItem, cart=cart, course=course)
    assert pre_req_course.type in cart.eligible_courses.filter(eligible=False)
    assert course.type in cart.eligible_courses.filter(eligible=False)

    course_cart_item.delete()
    course.participants.add(cart.user)
    assert pre_req_course.type in cart.eligible_courses.filter(eligible=False)
    assert course.type in cart.eligible_courses.filter(eligible=False)


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
