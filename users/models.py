"""The single User model shared by clients, service providers and admins."""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.choices import District


class User(AbstractUser):
    class Role(models.TextChoices):
        CLIENT = "CLIENT", _("Client")
        PROVIDER = "PROVIDER", _("Service Provider")
        ADMIN = "ADMIN", _("Admin")

    class AccountStatus(models.TextChoices):
        ACTIVE = "ACTIVE", _("Active")
        SUSPENDED = "SUSPENDED", _("Suspended")
        DEACTIVATED = "DEACTIVATED", _("Deactivated")

    class Language(models.TextChoices):
        ENGLISH = "en", _("English")
        FRENCH = "fr", _("French")

    class Theme(models.TextChoices):
        LIGHT = "light", _("Light")
        DARK = "dark", _("Dark")

    role = models.CharField(
        max_length=20, choices=Role.choices, default=Role.CLIENT
    )
    email = models.EmailField(_("email address"), unique=True)
    phone = models.CharField(_("phone number"), max_length=20, blank=True)
    address = models.CharField(_("address"), max_length=255, blank=True)
    district = models.CharField(
        _("district"), max_length=30, choices=District.choices, blank=True
    )
    profile_picture = models.ImageField(upload_to="profiles/", blank=True)
    preferred_language = models.CharField(
        max_length=2, choices=Language.choices, default=Language.ENGLISH
    )
    theme = models.CharField(
        max_length=5, choices=Theme.choices, default=Theme.LIGHT
    )
    account_status = models.CharField(
        max_length=20,
        choices=AccountStatus.choices,
        default=AccountStatus.ACTIVE,
    )
    status_reason = models.CharField(max_length=255, blank=True)

    def save(self, *args, **kwargs):
        # Accounts made with "createsuperuser" are platform admins.
        if self.is_superuser:
            self.role = self.Role.ADMIN
        # Suspended and deactivated accounts cannot log in (FR 7.4).
        self.is_active = self.account_status == self.AccountStatus.ACTIVE
        super().save(*args, **kwargs)

    @property
    def is_client(self):
        return self.role == self.Role.CLIENT

    @property
    def is_provider(self):
        return self.role == self.Role.PROVIDER

    @property
    def is_platform_admin(self):
        return self.role == self.Role.ADMIN

    @property
    def display_name(self):
        return self.get_full_name() or self.email

    def __str__(self):
        return self.display_name
