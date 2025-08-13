from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include(("home.urls", "home"), namespace="home")),
    path("accounts/", include("allauth.urls")),
    path("i18n/", include("django.conf.urls.i18n")),    
]