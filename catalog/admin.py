from django.contrib import admin
from .models import (
    Category, Listing,
    Product, ProductVariant, Inventory, ProductGroup,
    Service, ServicePackage, ServiceRequest,
    Car, Property, Booking
)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "parent")
    search_fields = ("name", "slug")
    list_filter = ("parent",)
    prepopulated_fields = {"slug": ("name",)}

@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ("title", "type", "vendor", "category", "status", "is_active", "created_at")
    list_filter = ("type", "status", "is_active", "category")
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

@admin.register(ProductGroup)
class ProductGroupAdmin(admin.ModelAdmin):
    list_display = ("title", "vendor", "product_count", "created_at")
    search_fields = ("title", "vendor__display_name")
    list_filter = ("vendor",)
    filter_horizontal = ("products",)

    @admin.display(description="Products")
    def product_count(self, obj):
        return obj.products.count()

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

@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ("make", "model", "year", "vendor", "price", "is_active")
    list_filter = ("is_active", "vendor", "make", "fuel_type", "transmission", "condition")
    search_fields = ("make", "model", "vin", "vendor__display_name")

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ("title", "vendor", "city", "property_type", "purpose", "monthly_rent", "sale_price", "is_active")
    list_filter = ("city", "property_type", "purpose", "is_active", "vendor")
    search_fields = ("title", "city", "vendor__display_name")

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("bookable", "buyer", "start_date", "end_date", "quantity", "status", "total_price")
    list_filter = ("status", "start_date", "end_date")
    search_fields = ("buyer__username",)
