from django.shortcuts import render, get_object_or_404
from .models import Listing, Category

def listing_list(request):
    qs = Listing.objects.select_related("vendor", "category").filter(is_active=True)
    t = request.GET.get("type")
    q = request.GET.get("q")
    if t: qs = qs.filter(type=t)
    if q: qs = qs.filter(title__icontains=q)
    return render(request, "catalog/listing_list.html", {"listings": qs, "type": t, "q": q})

def listing_by_category(request, slug):
    cat = get_object_or_404(Category, slug=slug, parent__isnull=True)  # root categories for now
    qs = Listing.objects.select_related("vendor", "category").filter(is_active=True, category=cat)
    return render(request, "catalog/listing_list.html", {"listings": qs, "category": cat})

def listing_detail(request, slug):
    obj = get_object_or_404(
        Listing.objects.select_related("vendor", "category"),
        slug=slug, is_active=True
    )
    return render(request, "catalog/listing_detail.html", {"listing": obj})
