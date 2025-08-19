from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.core.exceptions import PermissionDenied
from .models import UserProfile, Vendor
from .forms import UserForm, UserProfileForm, SellerOnboardingForm

@login_required
def profile(request):
    profile = get_object_or_404(UserProfile, user=request.user)

    if request.method == "POST":
        user_form = UserForm(request.POST, instance=request.user)
        form = UserProfileForm(request.POST, instance=profile)
        if user_form.is_valid() and form.is_valid():
            user_form.save()
            form.save()
            messages.success(request, "Profile updated")
            return redirect("profiles:profile")
    else:
        user_form = UserForm(instance=request.user)
        form = UserProfileForm(instance=profile)

    return render(request, "profiles/profile.html", {
        "user_form": user_form,
        "form": form,
        "orders": None,
    })

def require_seller(user):
    p = getattr(user, "userprofile", None)
    v = getattr(user, "vendor", None)
    return bool(p and p.is_seller and v and v.is_active)

@login_required
def seller_onboarding(request):
    # If store exists already, branch on activation status
    v = getattr(request.user, "vendor", None)
    if v:
        # ensure flags
        prof = request.user.userprofile
        if not prof.is_seller:
            prof.is_seller = True
            prof.kyc_submitted = True
            prof.save(update_fields=["is_seller", "kyc_submitted"])
        if v.is_active:
            messages.info(request, "Your store is active.")
            return redirect("profiles:seller_dashboard")
        # pending/inactive → show pending page
        return render(request, "profiles/seller_pending.html", {"vendor": v})

    if request.method == "POST":
        form = SellerOnboardingForm(request.POST)
        if form.is_valid():
            vendor = form.save(commit=False)
            vendor.owner = request.user
            # new stores start inactive; activate in admin
            vendor.is_active = False
            vendor.save()
            prof = request.user.userprofile
            prof.is_seller = True
            prof.kyc_submitted = True
            prof.save(update_fields=["is_seller", "kyc_submitted"])
            messages.success(request, "Store submitted. Awaiting activation.")
            return render(request, "profiles/seller_pending.html", {"vendor": vendor})
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = SellerOnboardingForm(initial={"payout_provider": "manual"})
    return render(request, "profiles/seller_onboarding.html", {"form": form})

@login_required
def seller_dashboard(request):
    if not require_seller(request.user):
        messages.warning(request, "Seller onboarding required or store inactive.")
        return redirect("profiles:seller_onboarding")
    v = request.user.vendor
    from catalog.models import Listing
    listings = Listing.objects.filter(vendor=v).order_by("-created_at")[:20]
    return render(request, "profiles/seller_dashboard.html", {"vendor": v, "listings": listings})