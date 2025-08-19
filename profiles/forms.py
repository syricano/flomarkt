from django import forms
from django.contrib.auth.models import User
from django_countries.widgets import CountrySelectWidget
from django.utils.text import slugify
from .models import UserProfile, Vendor


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
        }


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            "first_name",
            "last_name",
            "phone_number",
            "email",
            "postcode",
            "town_or_city",
            "county",
            "street_address1",
            "street_address2",
            "country",
        ]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "phone_number": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "postcode": forms.TextInput(attrs={"class": "form-control"}),
            "town_or_city": forms.TextInput(attrs={"class": "form-control"}),
            "county": forms.TextInput(attrs={"class": "form-control"}),
            "street_address1": forms.TextInput(attrs={"class": "form-control"}),
            "street_address2": forms.TextInput(attrs={"class": "form-control"}),
            "country": CountrySelectWidget(attrs={"class": "form-select"}),
        }


def _unique_slug(base: str) -> str:
    base = slugify(base or "store")
    slug = base or "store"
    i = 2
    while Vendor.objects.filter(slug=slug).exists():
        slug = f"{base}-{i}"
        i += 1
    return slug

class SellerOnboardingForm(forms.ModelForm):
    # make slug optional; we’ll auto-fill if missing
    slug = forms.SlugField(required=False)
    accept_terms = forms.BooleanField(required=True, label="I accept the seller terms")

    class Meta:
        model = Vendor
        fields = ["display_name", "slug", "bio", "payout_provider", "payout_account_id"]
        widgets = {
            "display_name": forms.TextInput(attrs={"class": "form-control"}),
            "slug": forms.TextInput(attrs={"class": "form-control"}),
            "bio": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "payout_provider": forms.TextInput(attrs={"class": "form-control"}),
            "payout_account_id": forms.TextInput(attrs={"class": "form-control"}),
        }

    def clean_slug(self):
        slug = self.cleaned_data.get("slug")
        name = self.cleaned_data.get("display_name")
        if not slug:
            return _unique_slug(name)
        # ensure uniqueness if user typed a duplicate
        if Vendor.objects.filter(slug=slug).exists():
            raise forms.ValidationError("This slug is taken. Try another.")
        return slug