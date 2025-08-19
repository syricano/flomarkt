# catalog/admin.py
from django.contrib import admin
from .models import (
    Category, Listing,
    Product, ProductVariant, Inventory,
    Service, ServicePackage, ServiceRequest,
    Room, RentalItem, Property, Booking
)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "parent")
    search_fields = ("name", "slug")
    list_filter = ("parent",)
    prepopulated_fields = {"slug": ("name",)}

@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ("title", "type", "vendor", "category", "is_active", "created_at")
    list_filter = ("type", "is_active", "category")
    search_fields = ("title", "vendor__display_name", "slug")
    autocomplete_fields = ("category", "vendor")
    readonly_fields = ("created_at",)
    prepopulated_fields = {"slug": ("title",)}

class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "vendor", "sku", "base_price")
    search_fields = ("name", "sku", "vendor__display_name")
    list_filter = ("vendor",)
    inlines = (ProductVariantInline,)

@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ("product", "sku", "price")
    search_fields = ("sku", "product__name")
    list_filter = ("product",)

@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ("variant", "quantity")
    search_fields = ("variant__sku", "variant__product__name")

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "vendor", "pricing_type", "hourly_rate", "base_fixed_price", "is_active")
    list_filter = ("pricing_type", "is_active", "vendor")
    search_fields = ("name", "vendor__display_name")

@admin.register(ServicePackage)
class ServicePackageAdmin(admin.ModelAdmin):
    list_display = ("service", "title", "price", "delivery_days", "is_active")
    list_filter = ("is_active", "delivery_days")
    search_fields = ("service__name", "title")

@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "service", "buyer", "status", "quoted_price", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("service__name", "buyer__username")

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("name", "vendor", "location", "capacity", "nightly_price", "is_active")
    list_filter = ("is_active", "vendor", "capacity")
    search_fields = ("name", "location", "vendor__display_name")

@admin.register(RentalItem)
class RentalItemAdmin(admin.ModelAdmin):
    list_display = ("name", "vendor", "daily_price", "deposit", "quantity", "is_active")
    list_filter = ("is_active", "vendor")
    search_fields = ("name", "vendor__display_name", "location")

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ("title", "vendor", "city", "is_for_rent", "monthly_rent", "sale_price", "is_active")
    list_filter = ("city", "is_for_rent", "is_active", "vendor")
    search_fields = ("title", "city", "vendor__display_name")

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("bookable", "buyer", "start_date", "end_date", "quantity", "status", "total_price")
    list_filter = ("status", "start_date", "end_date")
    search_fields = ("buyer__username",)
