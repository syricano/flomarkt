from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.text import slugify

from .models import (
    Listing, Category,
    Product, ProductGroup,
    Service, Car, Property,
)
from .forms_seller import (
    TypeSelectForm, BaseListingForm,
    ProductLineFormSet,
    ServiceForm, CarForm, PropertyForm,
)

# ---------- helpers ----------
TYPE_TO_CATEGORY_SLUG = {
    "PRODUCT": "products",
    "SERVICE": "services",
    "CAR": "cars",
    "PROPERTY": "real-estate",
}

def _category_for_type(t: str) -> Category:
    slug = TYPE_TO_CATEGORY_SLUG[t]
    cat = Category.objects.filter(slug=slug, parent__isnull=True).order_by("id").first()
    if not cat:
        cat = Category.objects.create(slug=slug, name=slug.replace("-", " ").title(), parent=None)
    return cat

def require_seller(user):
    return bool(getattr(user, "vendor", None))

def _unique_sku(seed: str) -> str:
    base = slugify(seed)[:12].upper()
    return f"{base}-{get_random_string(6).upper()}"

def listing_key(obj):
    return f"{obj.__class__.__name__.lower()}-{obj.pk}"

# ---------- views ----------
@login_required
def my_listings(request):
    if not require_seller(request.user):
        return redirect("profiles:seller_onboarding")
    v = request.user.vendor
    qs = Listing.objects.select_related("category").filter(vendor=v).order_by("-created_at")
    t = request.GET.get("type")
    if t:
        qs = qs.filter(type=t)
    return render(request, "catalog/seller/my_listings.html", {"listings": qs, "type": t})

@login_required
def listing_create(request):
    if not require_seller(request.user):
        return redirect("profiles:seller_onboarding")

    # Step 1: choose type
    if request.method == "GET" and "type" not in request.GET:
        return render(request, "catalog/seller/create_select_type.html", {"form": TypeSelectForm()})

    chosen_type = request.GET.get("type") if request.method == "GET" else request.POST.get("type")
    category = _category_for_type(chosen_type)

    # Step 2: render forms
    if request.method == "GET":
        ctx = {
            "type": chosen_type,
            "category": category,
            "base": BaseListingForm(),
            # exactly one blank product row on first render
            "pformset": (
                ProductLineFormSet(prefix="products", initial=[{}])
                if chosen_type == "PRODUCT" else None
            ),
            "subform": (
                ServiceForm() if chosen_type == "SERVICE" else
                CarForm() if chosen_type == "CAR" else
                PropertyForm() if chosen_type == "PROPERTY" else
                None
            ),
        }
        return render(request, "catalog/seller/create_fill_forms.html", ctx)

    # POST
    base = BaseListingForm(request.POST)
    if chosen_type == "PRODUCT":
        pset = ProductLineFormSet(request.POST, prefix="products")
        subform = None
    else:
        pset = None
        subform = (
            ServiceForm(request.POST) if chosen_type == "SERVICE" else
            CarForm(request.POST) if chosen_type == "CAR" else
            PropertyForm(request.POST) if chosen_type == "PROPERTY" else
            None
        )

    valid = base.is_valid() and ((pset and pset.is_valid()) or (subform and subform.is_valid()))
    if not valid:
        messages.error(request, "Please fix errors below.")
        return render(request, "catalog/seller/create_fill_forms.html", {
            "type": chosen_type, "category": category, "base": base, "pformset": pset, "subform": subform,
        })

    vendor = request.user.vendor
    title = base.cleaned_data["title"]
    teaser = base.cleaned_data.get("short_description") or ""
    currency = base.cleaned_data.get("currency") or "EUR"

    if chosen_type == "PRODUCT":
        group = ProductGroup.objects.create(vendor=vendor, title=title)
        for f in pset.forms:
            if not getattr(f, "cleaned_data", None):  # empty row
                continue
            if f.cleaned_data.get("DELETE"):
                continue
            name = f.cleaned_data["name"]
            price = f.cleaned_data["price"]
            sku = f.cleaned_data.get("sku") or _unique_sku(name)
            prod = Product.objects.create(
                vendor=vendor,
                name=name,
                sku=sku,
                base_price=price,
            )
            group.products.add(prod)
        obj = group
    else:
        obj = subform.save(commit=False)
        if hasattr(obj, "vendor"):
            obj.vendor = vendor
        obj.save()

    listing = Listing.objects.create(
        title=title,
        slug=slugify(f"{title}-{listing_key(obj)}")[:50],
        type=chosen_type,
        category=category,
        vendor=vendor,
        is_active=False,
        status=Listing.Status.DRAFT,
        teaser=teaser,
        currency=currency,
        content_object=obj,
    )
    messages.success(request, "Draft created. Review and submit.")
    return redirect("catalog:seller_listing_review", pk=listing.pk)

@login_required
def listing_review(request, pk: int):
    if not require_seller(request.user):
        return redirect("profiles:seller_onboarding")
    v = request.user.vendor
    l = get_object_or_404(Listing.objects.select_related("category"), pk=pk, vendor=v)
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "submit":
            l.status = Listing.Status.PENDING
            l.submitted_at = timezone.now()
            l.is_active = False
            l.save(update_fields=["status", "submitted_at", "is_active"])
            messages.success(request, "Listing submitted for review.")
            return redirect("catalog:seller_my_listings")
        if action == "edit":
            return redirect("catalog:seller_my_listings")
    return render(request, "catalog/seller/review.html", {"listing": l})
