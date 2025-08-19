from django.urls import path
from . import views

app_name = "catalog"
urlpatterns = [
    path("", views.listing_list, name="listing_list"),
    path("c/<slug:slug>/", views.listing_by_category, name="category"),
    path("<slug:slug>/", views.listing_detail, name="listing_detail"),
]
