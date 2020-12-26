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

from registration import rest_router
from registration import urls as reg_urls

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include(reg_urls)),
    path("accounts/", include(auth_urls)),
    path("api-auth/", include(urls)),
    path("api/", include(rest_router.router.urls)),
]

urlpatterns += staticfiles_urlpatterns()
