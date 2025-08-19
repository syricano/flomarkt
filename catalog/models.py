# catalog/models.py
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


# -------------------------------
# Core taxonomy
# -------------------------------
class Category(models.Model):
    name = models.CharField(_("Name"), max_length=120)
    slug = models.SlugField(_("Slug"))
    parent = models.ForeignKey(
        "self", null=True, blank=True, related_name="children", on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")
        unique_together = (("slug", "parent"),)
        indexes = [models.Index(fields=["parent", "slug"])]

    def __str__(self) -> str:
        return self.name


# -------------------------------
# Marketplace wrapper
# -------------------------------
class Listing(models.Model):
    class Type(models.TextChoices):
        PRODUCT = "PRODUCT", _("Product")
        SERVICE = "SERVICE", _("Service")
        ROOM = "ROOM", _("Room/Hotel")
        RENTAL_ITEM = "RENTAL_ITEM", _("Rental")
        PROPERTY = "PROPERTY", _("Property")
        CAR = "CAR", _("Car")

    title = models.CharField(_("Title"), max_length=180)
    slug = models.SlugField(_("Slug"), unique=True)
    type = models.CharField(_("Type"), max_length=16, choices=Type.choices)
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="listings", verbose_name=_("Category")
    )
    vendor = models.ForeignKey(
        "profiles.Vendor", on_delete=models.PROTECT, related_name="listings", verbose_name=_("Vendor")
    )
    is_active = models.BooleanField(_("Active"), default=True)
    teaser = models.TextField(_("Teaser"), blank=True)
    hero_image = models.ImageField(_("Hero image"), upload_to="listing/", blank=True, null=True)

    # Generic link to the concrete object
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveBigIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Listing")
        verbose_name_plural = _("Listings")
        indexes = [
            models.Index(fields=["type", "is_active"]),
            models.Index(fields=["category"]),
            models.Index(fields=["vendor"]),
            models.Index(fields=["slug"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} [{self.type}]"


# -------------------------------
# Products (+ variants and stock)
# -------------------------------
class Product(models.Model):
    vendor = models.ForeignKey(
        "profiles.Vendor", on_delete=models.PROTECT, related_name="products", verbose_name=_("Vendor")
    )
    name = models.CharField(_("Name"), max_length=180)
    sku = models.CharField(_("SKU"), max_length=64, unique=True)
    base_price = models.DecimalField(_("Base price"), max_digits=10, decimal_places=2)
    data = models.JSONField(_("Attributes"), default=dict, blank=True)  # free-form attributes

    class Meta:
        verbose_name = _("Product")
        verbose_name_plural = _("Products")
        indexes = [models.Index(fields=["sku"])]

    def __str__(self) -> str:
        return self.name


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    sku = models.CharField(_("SKU"), max_length=64, unique=True)
    price = models.DecimalField(_("Price"), max_digits=10, decimal_places=2)
    options = models.JSONField(_("Options"), default=dict, blank=True)  # e.g. {"color":"red","size":"M"}

    class Meta:
        verbose_name = _("Product variant")
        verbose_name_plural = _("Product variants")

    def __str__(self) -> str:
        return f"{self.product.name} / {self.sku}"


class Inventory(models.Model):
    variant = models.OneToOneField(
        ProductVariant, on_delete=models.CASCADE, related_name="inventory"
    )
    quantity = models.PositiveIntegerField(_("Quantity"), default=0)

    class Meta:
        verbose_name = _("Inventory")
        verbose_name_plural = _("Inventory")

    def __str__(self) -> str:
        return f"{self.variant.sku}: {self.quantity}"


# -------------------------------
# Services (+ packages, RFQs)
# -------------------------------
class Service(models.Model):
    class PricingType(models.TextChoices):
        HOURLY = "HOURLY", _("Hourly")
        FIXED = "FIXED", _("Fixed")
        MIXED = "MIXED", _("Mixed")

    vendor = models.ForeignKey(
        "profiles.Vendor", on_delete=models.PROTECT, related_name="services", verbose_name=_("Vendor")
    )
    name = models.CharField(_("Name"), max_length=160)
    pricing_type = models.CharField(
        _("Pricing type"), max_length=8, choices=PricingType.choices, default=PricingType.HOURLY
    )
    hourly_rate = models.DecimalField(_("Hourly rate"), max_digits=10, decimal_places=2, null=True, blank=True)
    min_hours = models.PositiveIntegerField(_("Minimum billable hours"), default=1)
    base_fixed_price = models.DecimalField(_("Base fixed price"), max_digits=10, decimal_places=2, null=True, blank=True)

    is_remote = models.BooleanField(_("Remote available"), default=True)
    service_area = models.CharField(_("Service area"), max_length=160, blank=True)  # e.g. "Berlin" or "Remote"
    skills = models.JSONField(_("Skills/tags"), default=list, blank=True)           # ["React","Django"]
    details = models.JSONField(_("Details"), default=dict, blank=True)
    portfolio_url = models.URLField(_("Portfolio URL"), blank=True)
    is_active = models.BooleanField(_("Active"), default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Service")
        verbose_name_plural = _("Services")

    def __str__(self) -> str:
        return self.name


class ServicePackage(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="packages")
    title = models.CharField(_("Title"), max_length=140)
    description = models.TextField(_("Description"), blank=True)
    price = models.DecimalField(_("Price"), max_digits=10, decimal_places=2)
    delivery_days = models.PositiveIntegerField(_("Delivery days"), default=7)
    inclusions = models.JSONField(_("Inclusions"), default=list, blank=True)
    revisions = models.PositiveIntegerField(_("Revisions"), default=1)
    is_active = models.BooleanField(_("Active"), default=True)

    class Meta:
        verbose_name = _("Service package")
        verbose_name_plural = _("Service packages")

    def __str__(self) -> str:
        return f"{self.service.name} · {self.title}"


class ServiceRequest(models.Model):
    PENDING, QUOTED, ACCEPTED, REJECTED, CANCELED = (
        "PENDING",
        "QUOTED",
        "ACCEPTED",
        "REJECTED",
        "CANCELED",
    )
    STATUS_CHOICES = [
        (PENDING, _("Pending")),
        (QUOTED, _("Quoted")),
        (ACCEPTED, _("Accepted")),
        (REJECTED, _("Rejected")),
        (CANCELED, _("Canceled")),
    ]

    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="requests")
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="service_requests")
    brief = models.TextField(_("Brief"))
    attachments = models.JSONField(_("Attachments"), default=list, blank=True)  # store paths/keys if you add uploads
    status = models.CharField(_("Status"), max_length=10, choices=STATUS_CHOICES, default=PENDING)
    quoted_price = models.DecimalField(_("Quoted price"), max_digits=10, decimal_places=2, null=True, blank=True)
    estimated_days = models.PositiveIntegerField(_("Estimated days"), null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Service request")
        verbose_name_plural = _("Service requests")

    def __str__(self) -> str:
        return f"Request #{self.id} for {self.service.name}"


# -------------------------------
# Rooms · Rentals · Property
# -------------------------------
class Room(models.Model):
    vendor = models.ForeignKey(
        "profiles.Vendor", on_delete=models.PROTECT, related_name="rooms", verbose_name=_("Vendor")
    )
    name = models.CharField(_("Name"), max_length=160)
    location = models.CharField(_("Location"), max_length=200)
    capacity = models.PositiveIntegerField(_("Capacity"), default=1)
    nightly_price = models.DecimalField(_("Nightly price"), max_digits=10, decimal_places=2)
    amenities = models.JSONField(_("Amenities"), default=list, blank=True)
    is_active = models.BooleanField(_("Active"), default=True)

    class Meta:
        verbose_name = _("Room")
        verbose_name_plural = _("Rooms")

    def __str__(self) -> str:
        return self.name


class RentalItem(models.Model):
    vendor = models.ForeignKey(
        "profiles.Vendor", on_delete=models.PROTECT, related_name="rental_items", verbose_name=_("Vendor")
    )
    name = models.CharField(_("Name"), max_length=160)
    daily_price = models.DecimalField(_("Daily price"), max_digits=10, decimal_places=2)
    deposit = models.DecimalField(_("Deposit"), max_digits=10, decimal_places=2, default=0)
    quantity = models.PositiveIntegerField(_("Units available"), default=1)
    location = models.CharField(_("Pickup location"), max_length=200, blank=True)
    specs = models.JSONField(_("Specs"), default=dict, blank=True)
    media = models.JSONField(_("Media"), default=list, blank=True)
    is_active = models.BooleanField(_("Active"), default=True)

    class Meta:
        verbose_name = _("Rental item")
        verbose_name_plural = _("Rental items")

    def __str__(self) -> str:
        return self.name


class Property(models.Model):
    vendor = models.ForeignKey(
        "profiles.Vendor", on_delete=models.PROTECT, related_name="properties", verbose_name=_("Vendor")
    )
    title = models.CharField(_("Title"), max_length=180)
    address = models.CharField(_("Address"), max_length=220)
    city = models.CharField(_("City"), max_length=120)
    lat = models.DecimalField(_("Latitude"), max_digits=9, decimal_places=6, null=True, blank=True)
    lng = models.DecimalField(_("Longitude"), max_digits=9, decimal_places=6, null=True, blank=True)
    bedrooms = models.PositiveIntegerField(_("Bedrooms"), default=0)
    bathrooms = models.PositiveIntegerField(_("Bathrooms"), default=0)
    area_sqm = models.DecimalField(_("Area (m²)"), max_digits=8, decimal_places=2, null=True, blank=True)

    is_for_rent = models.BooleanField(_("For rent"), default=False)
    monthly_rent = models.DecimalField(_("Monthly rent"), max_digits=12, decimal_places=2, null=True, blank=True)
    sale_price = models.DecimalField(_("Sale price"), max_digits=12, decimal_places=2, null=True, blank=True)
    deposit = models.DecimalField(_("Deposit"), max_digits=12, decimal_places=2, null=True, blank=True)

    features = models.JSONField(_("Features"), default=list, blank=True)
    media = models.JSONField(_("Media"), default=list, blank=True)
    is_active = models.BooleanField(_("Active"), default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Property")
        verbose_name_plural = _("Properties")

    def __str__(self) -> str:
        return self.title


# -------------------------------
# Booking (generic, for bookables)
# -------------------------------
class Booking(models.Model):
    # bookable → Room or RentalItem (extendable to others)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveBigIntegerField()
    bookable = GenericForeignKey("content_type", "object_id")

    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookings")
    start_date = models.DateField(_("Start date"))
    end_date = models.DateField(_("End date"))
    quantity = models.PositiveIntegerField(_("Quantity"), default=1)

    total_price = models.DecimalField(_("Total price"), max_digits=12, decimal_places=2)
    status = models.CharField(
        _("Status"),
        max_length=16,
        choices=[("PENDING", _("Pending")), ("CONFIRMED", _("Confirmed")), ("CANCELED", _("Canceled"))],
        default="PENDING",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Booking")
        verbose_name_plural = _("Bookings")
        indexes = [models.Index(fields=["content_type", "object_id", "start_date", "end_date"])]

    def __str__(self) -> str:
        return f"{self.bookable} [{self.start_date}→{self.end_date}]"
