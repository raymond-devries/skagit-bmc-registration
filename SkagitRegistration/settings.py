import json
import os
from distutils.util import strtobool
from pathlib import Path

import boto3
import dj_database_url
import sentry_sdk
import stripe
from django.contrib.messages import constants as messages
from django.urls import reverse_lazy
from sentry_sdk.integrations.django import DjangoIntegration

ENV_SECRETS_ID = os.environ["AWS_SECRETS_CONFIG_NAME"]
AWS_REGION = "us-west-2"
aws_session = boto3.session.Session()
client = aws_session.client(
    service_name="secretsmanager",
    region_name=AWS_REGION,
)
env_secrets = json.loads(
    client.get_secret_value(SecretId=ENV_SECRETS_ID)["SecretString"]
)
os.environ.update(env_secrets)

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")

DEBUG = strtobool(os.getenv("DEBUG", "false"))

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "console": {
            "format": "%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "console",
        },
    },
    "loggers": {
        "": {
            "level": "INFO",
            "handlers": ["console"],
        },
    },
}

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
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = not DEBUG

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

DATABASE_URL = os.getenv("DATABASE_URL")
DATABASES = {"default": dj_database_url.parse(DATABASE_URL)}

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

DB_BACKUP_BUCKET = os.getenv("DB_BACKUP_BUCKET")

if not DEBUG:
    STORAGES = {
        "staticfiles": {
            "BACKEND": "storages.backends.s3.S3Storage",
            "OPTIONS": {
                "bucket_name": os.getenv("STATIC_FILES_BUCKET_NAME"),
            },
        },
    }


def backup_filename(databasename, servername, datetime, extension, content_type):
    return f"'{databasename}-{datetime}.{extension}'"


DBBACKUP_FILENAME_TEMPLATE = backup_filename

LOGOUT_REDIRECT_URL = reverse_lazy("home")
LOGIN_REDIRECT_URL = reverse_lazy("home")

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

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
stripe.api_key = STRIPE_API_KEY

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    integrations=[DjangoIntegration()],
    traces_sample_rate=float(os.getenv("SENTRY_SAMPLE_RATE", 0)),
    send_default_pii=True,
)
