from datetime import datetime, timedelta

import pytest
from faker import Faker
from model_bakery import baker

from registration import models


@pytest.fixture
def fake() -> Faker:
    Faker.seed(0)
    return Faker()


@pytest.fixture(autouse=True)
def patch_stripe(monkeypatch):
    class FakeCustomer:
        @property
        def stripe_id(self):
            return "fake_customer"

    def create_customer(*args, **kwargs):
        return FakeCustomer

    monkeypatch.setattr("stripe.Customer.create", create_customer)


@pytest.fixture
def registration_settings():
    baker.make(
        models.RegistrationSettings,
        early_registration_open=datetime(year=2022, month=1, day=1),
        registration_open=datetime(year=2022, month=1, day=10),
        registration_close=datetime(year=2022, month=3, day=1),
        refund_period=timedelta(days=14),
    )


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
