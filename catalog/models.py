from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django_countries.fields import CountryField


# ---------- Constants ----------
CURRENCY_CHOICES = [
    ("EUR", "EUR"), ("USD", "USD"), ("GBP", "GBP"), ("AED", "AED"), ("SAR", "SAR"),
    ("JPY", "JPY"), ("CNY", "CNY"), ("INR", "INR"), ("AUD", "AUD"), ("CAD", "CAD"),
    ("CHF", "CHF"), ("SEK", "SEK"), ("NOK", "NOK"), ("DKK", "DKK"), ("TRY", "TRY"),
]


# ---------- Taxonomy ----------
class Category(models.Model):
    name = models.CharField(_("Name"), max_length=120)
    slug = models.SlugField(_("Slug"))
    parent = models.ForeignKey(
        "self", null=True, blank=True, related_name="children", on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")
        constraints = [
            models.UniqueConstraint(fields=["slug", "parent"], name="uniq_slug_per_parent"),
            models.UniqueConstraint(
                fields=["slug"],
                condition=Q(parent__isnull=True),
                name="uniq_root_slug",
            ),
        ]
        indexes = [models.Index(fields=["parent", "slug"])]

    def __str__(self) -> str:
        return self.name


# ---------- Marketplace wrapper ----------
class Listing(models.Model):
    class Type(models.TextChoices):
        PRODUCT = "PRODUCT", _("Product")
        SERVICE = "SERVICE", _("Service")
        CAR = "CAR", _("Car")
        PROPERTY = "PROPERTY", _("Real Estate")

    class Status(models.TextChoices):
        DRAFT = "DRAFT", _("Draft")
        PENDING = "PENDING", _("Pending review")
        PUBLISHED = "PUBLISHED", _("Published")
        REJECTED = "REJECTED", _("Rejected")

    title = models.CharField(_("Title"), max_length=180)
    slug = models.SlugField(_("Slug"), unique=True)
    type = models.CharField(_("Type"), max_length=16, choices=Type.choices)
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="listings", verbose_name=_("Category")
    )
    vendor = models.ForeignKey(
        "profiles.Vendor", on_delete=models.PROTECT, related_name="listings", verbose_name=_("Vendor")
    )

    status = models.CharField(_("Status"), max_length=12, choices=Status.choices, default=Status.DRAFT)
    review_notes = models.TextField(_("Review notes"), blank=True)
    submitted_at = models.DateTimeField(_("Submitted at"), null=True, blank=True)
    published_at = models.DateTimeField(_("Published at"), null=True, blank=True)

    is_active = models.BooleanField(_("Active"), default=True)
    teaser = models.TextField(_("Teaser"), blank=True)
    hero_image = models.ImageField(_("Hero image"), upload_to="listing/", blank=True, null=True)

    # Context
    country = CountryField(_("Country"), blank=True, null=True)
    currency = models.CharField(_("Currency"), max_length=3, choices=CURRENCY_CHOICES, default="EUR")

    # Generic link to concrete object
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveBigIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Listing")
        verbose_name_plural = _("Listings")
        indexes = [
            models.Index(fields=["type", "is_active"]),
            models.Index(fields=["status"]),
            models.Index(fields=["category"]),
            models.Index(fields=["vendor"]),
            models.Index(fields=["slug"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} [{self.type}]"


# ---------- Products ----------
class Product(models.Model):
    vendor = models.ForeignKey(
        "profiles.Vendor", on_delete=models.PROTECT, related_name="products", verbose_name=_("Vendor")
    )
    name = models.CharField(_("Name"), max_length=180)
    sku = models.CharField(_("Item code / SKU"), max_length=64, unique=True)
    base_price = models.DecimalField(_("Base price"), max_digits=10, decimal_places=2, null=True, blank=True)
    data = models.JSONField(_("Attributes"), default=dict, blank=True)

    class Meta:
        verbose_name = _("Product")
        verbose_name_plural = _("Products")
        indexes = [models.Index(fields=["sku"])]

    def __str__(self) -> str:
        return self.name


class ProductGroup(models.Model):
    vendor = models.ForeignKey(
        "profiles.Vendor", on_delete=models.PROTECT, related_name="product_groups", verbose_name=_("Vendor")
    )
    title = models.CharField(_("Title"), max_length=180)
    description = models.TextField(_("Description"), blank=True)
    products = models.ManyToManyField(Product, related_name="groups", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Product group")
        verbose_name_plural = _("Product groups")

    def __str__(self) -> str:
        return self.title


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    sku = models.CharField(_("Variant code"), max_length=64, unique=True)
    price = models.DecimalField(_("Price"), max_digits=10, decimal_places=2)
    options = models.JSONField(_("Options"), default=dict, blank=True)

    class Meta:
        verbose_name = _("Product variant")
        verbose_name_plural = _("Product variants")

    def __str__(self) -> str:
        return f"{self.product.name} / {self.sku}"


class Inventory(models.Model):
    variant = models.OneToOneField(ProductVariant, on_delete=models.CASCADE, related_name="inventory")
    quantity = models.PositiveIntegerField(_("Quantity"), default=0)

    class Meta:
        verbose_name = _("Inventory")
        verbose_name_plural = _("Inventory")

    def __str__(self) -> str:
        return f"{self.variant.sku}: {self.quantity}"


# ---------- Services ----------
class Service(models.Model):
    class PricingType(models.TextChoices):
        HOURLY = "HOURLY", _("Hourly")
        FIXED = "FIXED", _("Fixed")
        MIXED = "MIXED", _("Mixed")

    vendor = models.ForeignKey(
        "profiles.Vendor", on_delete=models.PROTECT, related_name="services", verbose_name=_("Vendor")
    )
    name = models.CharField(_("Name"), max_length=160)
    pricing_type = models.CharField(_("Pricing type"), max_length=8, choices=PricingType.choices, default=PricingType.HOURLY)
    hourly_rate = models.DecimalField(_("Hourly rate"), max_digits=10, decimal_places=2, null=True, blank=True)
    min_hours = models.PositiveIntegerField(_("Minimum billable hours"), default=1)
    base_fixed_price = models.DecimalField(_("Base fixed price"), max_digits=10, decimal_places=2, null=True, blank=True)

    is_remote = models.BooleanField(_("Remote available"), default=True)
    service_area = models.CharField(_("Service area"), max_length=160, blank=True)
    skills = models.JSONField(_("Skills/tags"), default=list, blank=True)
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
    PENDING, QUOTED, ACCEPTED, REJECTED, CANCELED = ("PENDING", "QUOTED", "ACCEPTED", "REJECTED", "CANCELED")
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
    attachments = models.JSONField(_("Attachments"), default=list, blank=True)
    status = models.CharField(_("Status"), max_length=10, choices=STATUS_CHOICES, default=PENDING)
    quoted_price = models.DecimalField(_("Quoted price"), max_digits=10, decimal_places=2, null=True, blank=True)
    estimated_days = models.PositiveIntegerField(_("Estimated days"), null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Service request")
        verbose_name_plural = _("Service requests")

    def __str__(self) -> str:
        return f"Request #{self.id} for {self.service.name}"


# ---------- Cars ----------
class Car(models.Model):
    class Transmission(models.TextChoices):
        MANUAL = "MANUAL", _("Manual")
        AUTOMATIC = "AUTOMATIC", _("Automatic")

    class Fuel(models.TextChoices):
        PETROL = "PETROL", _("Petrol")
        DIESEL = "DIESEL", _("Diesel")
        HYBRID = "HYBRID", _("Hybrid")
        ELECTRIC = "ELECTRIC", _("Electric")
        LPG = "LPG", _("LPG")
        CNG = "CNG", _("CNG")
        OTHER = "OTHER", _("Other")

    class Condition(models.TextChoices):
        NEW = "NEW", _("New")
        USED = "USED", _("Used")

    vendor = models.ForeignKey(
        "profiles.Vendor", on_delete=models.PROTECT, related_name="cars", verbose_name=_("Vendor")
    )
    make = models.CharField(_("Make"), max_length=80)
    model = models.CharField(_("Model"), max_length=80)
    year = models.PositiveIntegerField(_("Year"))
    made_in = CountryField(_("Made in"), blank=True, null=True)
    mileage_km = models.PositiveIntegerField(_("Mileage (km)"), default=0)
    transmission = models.CharField(_("Transmission"), max_length=12, choices=Transmission.choices, blank=True)
    fuel_type = models.CharField(_("Fuel type"), max_length=12, choices=Fuel.choices, blank=True)
    body_type = models.CharField(_("Body type"), max_length=50, blank=True)
    doors = models.PositiveSmallIntegerField(_("Doors"), null=True, blank=True)
    color = models.CharField(_("Color"), max_length=40, blank=True)
    condition = models.CharField(_("Condition"), max_length=8, choices=Condition.choices, default=Condition.USED)
    vin = models.CharField(_("VIN"), max_length=32, blank=True)
    price = models.DecimalField(_("Price"), max_digits=12, decimal_places=2)
    negotiable = models.BooleanField(_("Negotiable"), default=False)

    images = models.JSONField(_("Images"), default=list, blank=True)
    description = models.TextField(_("Description"), blank=True)
    is_active = models.BooleanField(_("Active"), default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Car")
        verbose_name_plural = _("Cars")

    def __str__(self) -> str:
        return f"{self.make} {self.model} {self.year}"


# ---------- Real Estate ----------
class Property(models.Model):
    class PropertyType(models.TextChoices):
        APARTMENT = "APARTMENT", _("Apartment")
        HOUSE = "HOUSE", _("House")
        LAND = "LAND", _("Land")
        COMMERCIAL = "COMMERCIAL", _("Commercial")

    class Purpose(models.TextChoices):
        SALE = "SALE", _("For sale")
        RENT = "RENT", _("For rent")

    vendor = models.ForeignKey(
        "profiles.Vendor", on_delete=models.PROTECT, related_name="properties", verbose_name=_("Vendor")
    )
    title = models.CharField(_("Title"), max_length=180)

    # Address + map
    address = models.CharField(_("Address"), max_length=220)
    city = models.CharField(_("City"), max_length=120)
    postal_code = models.CharField(_("Postal code"), max_length=20, blank=True)
    country = CountryField(_("Country"), blank=True, null=True)
    lat = models.DecimalField(_("Latitude"), max_digits=9, decimal_places=6, null=True, blank=True)
    lng = models.DecimalField(_("Longitude"), max_digits=9, decimal_places=6, null=True, blank=True)

    # Specs
    property_type = models.CharField(_("Property type"), max_length=16, choices=PropertyType.choices, default=PropertyType.APARTMENT)
    purpose = models.CharField(_("Purpose"), max_length=8, choices=Purpose.choices, default=Purpose.SALE)
    bedrooms = models.PositiveIntegerField(_("Bedrooms"), default=0)
    bathrooms = models.PositiveIntegerField(_("Bathrooms"), default=0)
    area_sqm = models.DecimalField(_("Area (m²)"), max_digits=8, decimal_places=2, null=True, blank=True)
    floor = models.CharField(_("Floor"), max_length=20, blank=True)
    year_built = models.PositiveIntegerField(_("Year built"), null=True, blank=True)
    furnished = models.BooleanField(_("Furnished"), default=False)
    heating = models.CharField(_("Heating"), max_length=80, blank=True)

    # Pricing
    monthly_rent = models.DecimalField(_("Monthly rent"), max_digits=12, decimal_places=2, null=True, blank=True)
    sale_price = models.DecimalField(_("Sale price"), max_digits=12, decimal_places=2, null=True, blank=True)
    deposit = models.DecimalField(_("Deposit"), max_digits=12, decimal_places=2, null=True, blank=True)

    # Media
    features = models.JSONField(_("Features"), default=list, blank=True)
    media = models.JSONField(_("Media"), default=list, blank=True)
    is_active = models.BooleanField(_("Active"), default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # deprecated legacy flag retained for compatibility
    is_for_rent = models.BooleanField(_("For rent (deprecated)"), default=False)

    class Meta:
        verbose_name = _("Property")
        verbose_name_plural = _("Properties")

    def __str__(self) -> str:
        return self.title


# ---------- Booking ----------
class Booking(models.Model):
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
