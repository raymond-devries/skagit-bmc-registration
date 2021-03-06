import pytest
from django.contrib.auth.models import User
from model_bakery import baker

from registration import models

pytestmark = pytest.mark.django_db

URLS = [
    ("/", (200, 200)),
    ("/available-courses/", (200, 200)),
    ("/registration/form/", (302, 200)),
    ("/registration/home/", (302, 200)),
    ("/registration/signup/", (302, 302)),
    ("/accounts/signup/", (200, 200)),
    ("/registration/cart/", (302, 200)),
    ("/accounts/login/", (200, 200)),
    ("/accounts/password_change/", (302, 200)),
    ("/accounts/password_change/done/", (302, 200)),
]


@pytest.fixture
def fill_db():
    baker.make(models.RegistrationSettings)


@pytest.mark.parametrize(["url", "status_code"], URLS)
def test_anonymous_access(fill_db, client, url, status_code):
    response = client.get(url)
    assert response.status_code == status_code[0]


@pytest.mark.parametrize(["url", "status_code"], URLS)
def test_logged_in_access(fill_db, client, url, status_code):
    client.force_login(User.objects.get_or_create(username="test_user")[0])
    response = client.get(url)
    assert response.status_code == status_code[1]
