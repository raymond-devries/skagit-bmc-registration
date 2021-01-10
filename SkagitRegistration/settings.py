import json
import os
from distutils.util import strtobool
from pathlib import Path

import dj_database_url
import sentry_sdk
from django.contrib.messages import constants as messages
from django.urls import reverse_lazy
from sentry_sdk.integrations.django import DjangoIntegration

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")

try:
    DEBUG = strtobool(os.getenv("DEBUG"))
except AttributeError:
    DEBUG = False

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS").split(",")

INTERNAL_IPS = ["127.0.0.1", "0.0.0.0"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "localflavor",
    "phonenumber_field",
    "bulma",
    "registration",
    "rest_framework",
    "django_extensions",
]

MIDDLEWARE = [
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "SkagitRegistration.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "SkagitRegistration.wsgi.application"

DATABASES = {"default": dj_database_url.parse(os.getenv("DATABASE_URL"))}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True

STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATIC_URL = "/static/"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

LOGOUT_REDIRECT_URL = reverse_lazy("home")
LOGIN_REDIRECT_URL = reverse_lazy("home")

DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL")

try:
    USE_AWS_EMAIL = strtobool(os.getenv("USE_AWS_EMAIL"))
except AttributeError:
    USE_AWS_EMAIL = False

if USE_AWS_EMAIL:
    EMAIL_USE_TLS = True
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = "email-smtp.us-west-2.amazonaws.com"
    EMAIL_PORT = 587
    EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
    EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

MESSAGE_TAGS = {messages.ERROR: "danger"}

DEFAULT_RENDERER_CLASSES = ("rest_framework.renderers.JSONRenderer",)

if DEBUG:
    DEFAULT_RENDERER_CLASSES = DEFAULT_RENDERER_CLASSES + (
        "rest_framework.renderers.BrowsableAPIRenderer",
    )

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ),
    "DEFAULT_RENDERER_CLASSES": DEFAULT_RENDERER_CLASSES,
}

PHONENUMBER_DEFAULT_REGION = "US"

STRIPE_API_KEY = os.getenv("STRIPE_API_KEY")
STRIPE_PUBLIC_API_KEY = os.getenv("STRIPE_PUBLIC_API_KEY")
STRIPE_ENDPOINT_SECRET = os.getenv("STRIPE_ENDPOINT_SECRET")

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    integrations=[DjangoIntegration()],
    traces_sample_rate=float(os.getenv("SENTRY_SAMPLE_RATE")),
    send_default_pii=True,
)
