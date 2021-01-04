import pytest
from model_bakery import baker

from registration import models


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
