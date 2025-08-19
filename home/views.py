from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext as _
from django.contrib import messages
from catalog.models import Listing


def index(request):
    latest = (
        Listing.objects.select_related("vendor", "category")
        .filter(is_active=True)
        .order_by("-created_at")[:8]
    )
    return render(request, "home/index.html", {"latest_listings": latest})

def about(request):
    return render(request, "home/about.html")

def contact(request):
    return render(request, "home/contact.html")

def terms(request):
    return render(request, "home/terms.html")

def privacy(request):
    return render(request, "home/privacy.html")
