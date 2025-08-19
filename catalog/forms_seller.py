from django import forms
from django.forms import formset_factory
from django.utils.translation import gettext_lazy as _
from django_countries.widgets import CountrySelectWidget

from .models import Service, Car, Property, CURRENCY_CHOICES


# ---------- Type selection ----------
TYPE_CHOICES = [
    ("PRODUCT", _("Product")),
    ("SERVICE", _("Service")),
    ("CAR", _("Car")),
    ("PROPERTY", _("Real Estate")),
]

class TypeSelectForm(forms.Form):
    type = forms.ChoiceField(
        label=_("What do you want to list?"),
        choices=TYPE_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"}),
    )


# ---------- Base listing fields ----------
class BaseListingForm(forms.Form):
    title = forms.CharField(
        label=_("Listing title"),
        max_length=180,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": _("add a name"),
        }),
    )
    short_description = forms.CharField(
        label=_("Short description"),
        required=False,
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 2,
            "placeholder": _("One-line summary"),
        }),
    )
    currency = forms.ChoiceField(
        label=_("Currency"),
        choices=CURRENCY_CHOICES,
        initial="EUR",
        widget=forms.Select(attrs={"class": "form-select"}),
    )


# ---------- Multi-product line items (for PRODUCT listings) ----------
COLOR_CHOICES = [
    ("", _("Color?")),
    ("black", _("Black")),
    ("white", _("White")),
    ("red", _("Red")),
    ("blue", _("Blue")),
    ("green", _("Green")),
]
SIZE_CHOICES = [("", _("Size?")), ("XS","XS"),("S","S"),("M","M"),("L","L"),("XL","XL")]

class ProductLineForm(forms.Form):
    name = forms.CharField(
        label=_("Product name"), max_length=180,
        widget=forms.TextInput(attrs={"class":"form-control","placeholder":_("e.g. Product name")})
    )
    sku = forms.CharField(
        label=_("Item code (optional)"), required=False,
        widget=forms.TextInput(attrs={"class":"form-control","placeholder":_("Leave empty to auto")})
    )
    price = forms.DecimalField(
        label=_("Price"), max_digits=10, decimal_places=2,
        widget=forms.NumberInput(attrs={"class":"form-control","step":"0.01","placeholder":"0.00"})
    )
    color = forms.ChoiceField(
        label=_("Color"), required=False, choices=COLOR_CHOICES,
        widget=forms.Select(attrs={"class":"form-select"})
    )
    size = forms.ChoiceField(
        label=_("Size"), required=False, choices=SIZE_CHOICES,
        widget=forms.Select(attrs={"class":"form-select"})
    )

ProductLineFormSet = formset_factory(
    ProductLineForm, extra=0, can_delete=True, min_num=1, validate_min=True
)



# ---------- Service ----------
class ServiceForm(forms.ModelForm):
    skills = forms.CharField(
        label=_("Skills/tags"),
        required=False,
        help_text=_("Comma-separated, e.g. Django, React"),
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    details = forms.CharField(
        label=_("Details"),
        required=False,
        help_text=_("Optional notes"),
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}),
    )

    class Meta:
        model = Service
        fields = [
            "name", "pricing_type", "hourly_rate", "min_hours",
            "base_fixed_price", "is_remote", "service_area",
            "skills", "details", "portfolio_url",
        ]
        labels = {
            "name": _("Service name"),
            "pricing_type": _("Pricing model"),
            "hourly_rate": _("Hourly rate"),
            "min_hours": _("Minimum hours"),
            "base_fixed_price": _("Fixed price"),
            "is_remote": _("Remote possible"),
            "service_area": _("Service area"),
            "portfolio_url": _("Portfolio URL"),
        }
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": _("e.g. Full-stack web dev")}),
            "pricing_type": forms.Select(attrs={"class": "form-select"}),
            "hourly_rate": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "min_hours": forms.NumberInput(attrs={"class": "form-control"}),
            "base_fixed_price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "is_remote": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "service_area": forms.TextInput(attrs={"class": "form-control", "placeholder": _("Berlin / Remote")}),
            "portfolio_url": forms.URLInput(attrs={"class": "form-control"}),
        }

    def clean_skills(self):
        s = self.cleaned_data.get("skills", "")
        return [t.strip() for t in s.split(",") if t.strip()]

    def clean_details(self):
        txt = self.cleaned_data.get("details", "").strip()
        return {"notes": txt} if txt else {}


# ---------- Car ----------
class CarForm(forms.ModelForm):
    images = forms.CharField(
        label=_("Images"), required=False,
        help_text=_("Comma-separated URLs or filenames"),
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": _("image1.jpg, image2.jpg")}),
    )

    class Meta:
        model = Car
        fields = [
            "make", "model", "year", "made_in", "mileage_km",
            "transmission", "fuel_type", "body_type", "doors", "color",
            "condition", "vin", "price", "negotiable", "images", "description", "is_active",
        ]
        labels = {
            "make": _("Make"),
            "model": _("Model"),
            "year": _("Year"),
            "made_in": _("Made in"),
            "mileage_km": _("Mileage (km)"),
            "transmission": _("Transmission"),
            "fuel_type": _("Fuel type"),
            "body_type": _("Body type"),
            "doors": _("Doors"),
            "color": _("Color"),
            "condition": _("Condition"),
            "vin": _("VIN"),
            "price": _("Price"),
            "negotiable": _("Negotiable"),
            "description": _("Description"),
            "is_active": _("Active"),
        }
        widgets = {
            "make": forms.TextInput(attrs={"class": "form-control", "placeholder": _("e.g. Volkswagen")}),
            "model": forms.TextInput(attrs={"class": "form-control", "placeholder": _("e.g. Golf")}),
            "year": forms.NumberInput(attrs={"class": "form-control", "placeholder": _("e.g. 2018")}),
            "made_in": CountrySelectWidget(attrs={"class": "form-select"}),
            "mileage_km": forms.NumberInput(attrs={"class": "form-control", "placeholder": _("e.g. 85000")}),
            "transmission": forms.Select(attrs={"class": "form-select"}),
            "fuel_type": forms.Select(attrs={"class": "form-select"}),
            "body_type": forms.TextInput(attrs={"class": "form-control", "placeholder": _("e.g. Hatchback")}),
            "doors": forms.NumberInput(attrs={"class": "form-control", "placeholder": _("e.g. 5")}),
            "color": forms.TextInput(attrs={"class": "form-control", "placeholder": _("e.g. White")}),
            "condition": forms.Select(attrs={"class": "form-select"}),
            "vin": forms.TextInput(attrs={"class": "form-control", "placeholder": _("optional")}),
            "price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "placeholder": "0.00"}),
            "negotiable": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": _("Additional notes")}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean_images(self):
        raw = self.cleaned_data.get("images", "")
        return [p.strip() for p in raw.split(",") if p.strip()]


# ---------- Property ----------
class PropertyForm(forms.ModelForm):
    features = forms.CharField(
        label=_("Features"),
        required=False,
        help_text=_("Comma-separated, e.g. balcony, elevator"),
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": _("balcony, elevator")}),
    )
    media = forms.CharField(
        label=_("Images"),
        required=False,
        help_text=_("Comma-separated URLs or filenames"),
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": _("image1.jpg, image2.jpg")}),
    )

    class Meta:
        model = Property
        fields = [
            "title", "property_type", "purpose",
            "address", "city", "postal_code", "country",
            "bedrooms", "bathrooms", "area_sqm", "floor", "year_built",
            "furnished", "heating",
            "monthly_rent", "sale_price", "deposit",
            "lat", "lng",
            "features", "media", "is_active",
        ]
        labels = {
            "title": _("Property title"),
            "property_type": _("Property type"),
            "purpose": _("Purpose"),
            "address": _("Address"),
            "city": _("City"),
            "postal_code": _("Postal code"),
            "country": _("Country"),
            "bedrooms": _("Bedrooms"),
            "bathrooms": _("Bathrooms"),
            "area_sqm": _("Area (m²)"),
            "floor": _("Floor"),
            "year_built": _("Year built"),
            "furnished": _("Furnished"),
            "heating": _("Heating"),
            "monthly_rent": _("Monthly rent"),
            "sale_price": _("Sale price"),
            "deposit": _("Deposit"),
            "lat": _("Latitude"),
            "lng": _("Longitude"),
            "is_active": _("Active"),
        }
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": _("e.g. 2BR near Alexanderplatz")}),
            "property_type": forms.Select(attrs={"class": "form-select"}),
            "purpose": forms.Select(attrs={"class": "form-select"}),
            "address": forms.TextInput(attrs={"class": "form-control", "placeholder": _("Street and number")}),
            "city": forms.TextInput(attrs={"class": "form-control", "placeholder": _("City")}),
            "postal_code": forms.TextInput(attrs={"class": "form-control", "placeholder": _("e.g. 10117")}),
            "country": CountrySelectWidget(attrs={"class": "form-select"}),
            "bedrooms": forms.NumberInput(attrs={"class": "form-control"}),
            "bathrooms": forms.NumberInput(attrs={"class": "form-control"}),
            "area_sqm": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "placeholder": _("e.g. 75")}),
            "floor": forms.TextInput(attrs={"class": "form-control", "placeholder": _("e.g. 3rd")}),
            "year_built": forms.NumberInput(attrs={"class": "form-control", "placeholder": _("e.g. 1998")}),
            "furnished": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "heating": forms.TextInput(attrs={"class": "form-control", "placeholder": _("e.g. Central")}),
            "monthly_rent": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "sale_price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "deposit": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "lat": forms.NumberInput(attrs={"class": "form-control", "step": "0.000001", "placeholder": _("map lat")}),
            "lng": forms.NumberInput(attrs={"class": "form-control", "step": "0.000001", "placeholder": _("map lng")}),
        }

    def clean_features(self):
        raw = self.cleaned_data.get("features", "")
        return [p.strip() for p in raw.split(",") if p.strip()]

    def clean_media(self):
        raw = self.cleaned_data.get("media", "")
        return [p.strip() for p in raw.split(",") if p.strip()]
