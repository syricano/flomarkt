# profiles/models.py
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django_countries.fields import CountryField
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify


class UserProfile(models.Model):
    """Default delivery info and order history"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name=_("User"))
    first_name = models.CharField(_("First name"), max_length=80, null=True, blank=True)
    last_name = models.CharField(_("Last name"), max_length=80, null=True, blank=True)
    phone_number = models.CharField(_("Phone number"), max_length=20, null=True, blank=True)
    email = models.EmailField(_("Email"), max_length=254, null=True, blank=True)

    postcode = models.CharField(_("Postcode"), max_length=20, null=True, blank=True)
    town_or_city = models.CharField(_("Town or city"), max_length=40, null=True, blank=True)
    street_address1 = models.CharField(_("Street address 1"), max_length=80, null=True, blank=True)
    street_address2 = models.CharField(_("Street address 2"), max_length=80, null=True, blank=True)
    county = models.CharField(_("County"), max_length=80, null=True, blank=True)
    country = CountryField(verbose_name=_("Country"), blank_label=_("Country *"), null=True, blank=True)

    # seller flags
    is_seller = models.BooleanField(default=False)
    kyc_submitted = models.BooleanField(default=False)
    kyc_approved = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username


class Vendor(models.Model):
    """One store per user. Gate listing creation with is_active."""
    owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name="vendor", verbose_name=_("Owner"))
    display_name = models.CharField(_("Display name"), max_length=120)
    slug = models.SlugField(_("Slug"), max_length=140, unique=True)
    bio = models.TextField(_("Bio"), blank=True)
    is_active = models.BooleanField(_("Active"), default=False)

    # payouts (fill later when wiring Stripe/PayPal)
    payout_provider = models.CharField(_("Payout provider"), max_length=32, blank=True)
    payout_account_id = models.CharField(_("Payout account id"), max_length=128, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Vendor")
        verbose_name_plural = _("Vendors")

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.display_name) or slugify(self.owner.username)
            self.slug = base
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.display_name


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    instance.userprofile.save()
