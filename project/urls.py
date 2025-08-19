from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include(("home.urls", "home"), namespace="home")),
    path("profiles/", include(("profiles.urls", "profiles"), namespace="profiles")),
    path("accounts/", include("allauth.urls")),
    path("catalog/", include(("catalog.urls", "catalog"), namespace="catalog")),
    path("i18n/", include("django.conf.urls.i18n")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)