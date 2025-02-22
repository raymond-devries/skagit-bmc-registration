"""SkagitRegistration URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.contrib.auth import urls as auth_urls
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path
from rest_framework import urls

from registration import rest_router, sign_up_urls
from registration import urls as reg_urls
from registration.instructor import instructor_urls
from registration.models import INSTRUCTOR_GROUP

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include(reg_urls)),
    path("accounts/", include(auth_urls)),
    path("accounts/", include(sign_up_urls)),
    path(
        f"{INSTRUCTOR_GROUP}/",
        include(
            (instructor_urls.url_patterns, "registration"), namespace=INSTRUCTOR_GROUP
        ),
    ),
    path("api-auth/", include(urls)),
    path("api/", include((rest_router.router.urls, "registration"), namespace="api")),
    path("api/", include(rest_router)),
]

urlpatterns += staticfiles_urlpatterns()
