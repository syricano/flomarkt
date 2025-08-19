# profiles/admin.py
from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import UserProfile, Vendor


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    fk_name = "user"
    can_delete = False
    extra = 0
    fields = (
        "first_name", "last_name", "email", "phone_number",
        "street_address1", "street_address2",
        "town_or_city", "county",
        "postcode", "country",
    )


class VendorInline(admin.StackedInline):
    model = Vendor
    fk_name = "owner"
    can_delete = True
    extra = 0
    fields = (
        "display_name", "slug", "bio",
        "is_active",
        "payout_provider", "payout_account_id",
    )
    prepopulated_fields = {"slug": ("display_name",)}


class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline, VendorInline)
    list_display = (
        "username", "email", "first_name", "last_name", "is_staff",
        "profile_phone", "profile_city", "profile_country",
        "vendor_store", "vendor_active",
    )
    search_fields = (
        "username", "email", "first_name", "last_name",
        "userprofile__phone_number",
        "userprofile__town_or_city",
        "vendor__display_name",
    )
    list_filter = BaseUserAdmin.list_filter + ("vendor__is_active",)

    @admin.display(description="Phone")
    def profile_phone(self, obj):
        up = getattr(obj, "userprofile", None)
        return up.phone_number if up and up.phone_number else ""

    @admin.display(description="City")
    def profile_city(self, obj):
        up = getattr(obj, "userprofile", None)
        return up.town_or_city if up and up.town_or_city else ""

    @admin.display(description="Country")
    def profile_country(self, obj):
        up = getattr(obj, "userprofile", None)
        if not up or not up.country:
            return ""
        return getattr(up.country, "name", str(up.country))

    @admin.display(description="Store")
    def vendor_store(self, obj):
        v = getattr(obj, "vendor", None)
        return v.display_name if v else ""

    @admin.display(boolean=True, description="Seller active")
    def vendor_active(self, obj):
        v = getattr(obj, "vendor", None)
        return bool(v and v.is_active)


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user", "first_name", "last_name",
        "phone_number", "town_or_city", "country",
    )
    list_select_related = ("user",)
    search_fields = (
        "user__username", "user__email",
        "first_name", "last_name",
        "phone_number", "town_or_city",
    )
    list_filter = ("country",)
    fieldsets = (
        (None, {"fields": ("user",)}),
        ("Contact", {"fields": (
            "first_name", "last_name",
            "email", "phone_number",
        )}),
        ("Address", {"fields": (
            "street_address1", "street_address2",
            "town_or_city", "county",
            "postcode", "country",
        )}),
    )


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ("display_name", "owner", "is_active", "created_at")
    list_select_related = ("owner",)
    search_fields = ("display_name", "owner__username", "owner__email")
    list_filter = ("is_active",)
    prepopulated_fields = {"slug": ("display_name",)}
