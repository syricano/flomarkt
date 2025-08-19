# catalog/urls.py (append seller routes)
from django.urls import path
from . import views
from . import views_seller

app_name = "catalog"
urlpatterns = [
    path("", views.listing_list, name="listing_list"),
    path("c/<slug:slug>/", views.listing_by_category, name="category"),
    path("<slug:slug>/", views.listing_detail, name="listing_detail"),

    # seller
    path("seller/listings/", views_seller.my_listings, name="seller_my_listings"),
    path("seller/listings/new/", views_seller.listing_create, name="seller_listing_create"),
    path("seller/listings/<int:pk>/review/", views_seller.listing_review, name="seller_listing_review"),
    # optional edit route later: seller_listing_edit
]
