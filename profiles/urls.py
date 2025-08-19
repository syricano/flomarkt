from django.urls import path
from . import views

app_name = 'profiles'
urlpatterns = [
    path("", views.profile, name="profile"),
    path("seller/onboarding/", views.seller_onboarding, name="seller_onboarding"),
    path("seller/dashboard/", views.seller_dashboard, name="seller_dashboard"),
]
