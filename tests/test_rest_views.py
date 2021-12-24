import pytest
from model_bakery import baker

from registration import models, rest_views

pytestmark = pytest.mark.django_db


def test_fulfill_order(create_registration_form):
    user = baker.make(models.User)
    create_registration_form(user)
    cart = models.UserCart.objects.get(user=user)
    baker.make(models.CartItem, cart=cart, _quantity=3)
    courses = models.Course.objects.filter(cartitem__cart=cart)
    course_ids = list(courses.values_list("id", flat=True))
    checkout_session_id = "123456789"
    payment_intent_id = "987654321"

    rest_views.fulfill_order(
        course_ids, user.id, checkout_session_id, payment_intent_id
    )
    assert not models.CartItem.objects.filter(cart=cart).exists()
    assert models.PaymentRecord.objects.filter(
        checkout_session_id=checkout_session_id, payment_intent_id=payment_intent_id
    ).exists()
    assert list(models.Course.objects.filter(participants=user)) == list(
        models.Course.objects.filter(id__in=course_ids)
    )
