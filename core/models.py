"""
All TrustyHands collections except User (which lives in users/models.py).

The names follow the ERD in the proposal. Fields marked "ERD addition"
were added because the Figma screens need them.
"""

import datetime
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Avg
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_mongodb_backend.fields import ArrayField

from core.choices import (
    Availability, ClientType, District, JobType, ProjectScale,
)

USER = settings.AUTH_USER_MODEL


# --- SERVICE_CATEGORY (FR 5.1 - 5.3) ---
class ServiceCategory(models.Model):
    class Group(models.TextChoices):
        TECHNICAL = "TECHNICAL", _("Technical Services")
        CREATIVE = "CREATIVE", _("Creative & Personal Services")

    name = models.CharField(max_length=80)
    slug = models.SlugField(max_length=80, unique=True)
    group = models.CharField(
        max_length=20, choices=Group.choices, default=Group.TECHNICAL
    )
    description = models.TextField(blank=True)
    icon = models.ImageField(upload_to="categories/", blank=True)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["display_order", "name"]
        verbose_name_plural = "service categories"

    def __str__(self):
        return self.name


# --- SERVICE_PROVIDER ---
class ServiceProvider(models.Model):
    class VerificationStatus(models.TextChoices):
        PENDING = "PENDING", _("Pending Verification")
        APPROVED = "APPROVED", _("Approved")
        REJECTED = "REJECTED", _("Rejected")
        MORE_INFO = "MORE_INFO", _("More Information Needed")

    class VerificationStage(models.TextChoices):
        BACKGROUND = "BACKGROUND", _("Background Check")
        IDENTITY = "IDENTITY", _("Identity Verification")
        LICENSE = "LICENSE", _("License Verification")
        INSURANCE = "INSURANCE", _("Insurance Check")

    user = models.OneToOneField(
        USER, on_delete=models.CASCADE, related_name="provider_profile"
    )
    business_name = models.CharField(max_length=120)
    profession_title = models.CharField(max_length=120, blank=True)
    bio = models.TextField(blank=True)
    categories = models.ManyToManyField(
        ServiceCategory, related_name="providers", blank=True
    )
    verification_status = models.CharField(
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
    )
    verification_stage = models.CharField(
        max_length=20,
        choices=VerificationStage.choices,
        default=VerificationStage.BACKGROUND,
    )
    rejection_reason = models.TextField(blank=True)
    availability = models.CharField(
        max_length=20,
        choices=Availability.choices,
        default=Availability.AVAILABLE,
    )
    average_rating = models.FloatField(default=0)
    review_count = models.PositiveIntegerField(default=0)
    completed_jobs_count = models.PositiveIntegerField(default=0)

    # ERD additions needed by the Figma screens
    cover_photo = models.ImageField(upload_to="providers/", blank=True)
    years_experience = models.PositiveIntegerField(default=0)
    district = models.CharField(
        max_length=30, choices=District.choices, blank=True
    )
    town = models.CharField(max_length=80, blank=True)
    areas_served = ArrayField(
        models.CharField(max_length=30), default=list, blank=True
    )
    client_type = models.CharField(
        max_length=20, choices=ClientType.choices, default=ClientType.BOTH
    )
    project_scale = models.CharField(
        max_length=10, choices=ProjectScale.choices,
        default=ProjectScale.MEDIUM,
    )
    main_specializations = models.TextField(blank=True)
    specialty_areas = models.TextField(blank=True)
    common_issues = models.TextField(blank=True)
    service_requirements = models.TextField(blank=True)
    process_notes = models.TextField(blank=True)
    bank_name = models.CharField(max_length=60, blank=True)
    bank_account_number = models.CharField(max_length=40, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.business_name

    @property
    def is_public(self):
        """Only approved, active providers are visible to clients."""
        return (
            self.verification_status == self.VerificationStatus.APPROVED
            and self.user.is_active
        )

    @property
    def location_label(self):
        return self.town or self.get_district_display()

    @property
    def tier(self):
        subscription = getattr(self, "subscription", None)
        return subscription.tier if subscription else Subscription.Tier.STARTER

    @property
    def bank_label(self):
        if not self.bank_account_number:
            return ""
        return f"{self.bank_name} ...{self.bank_account_number[-4:]}"

    def recalculate_rating(self):
        """FR 6.2: average rating is refreshed after every review change."""
        visible = self.reviews.filter(is_removed=False)
        self.review_count = visible.count()
        average = visible.aggregate(avg=Avg("rating"))["avg"] or 0
        self.average_rating = round(average, 1)
        self.save(update_fields=["review_count", "average_rating"])

    def recalculate_completed_jobs(self):
        self.completed_jobs_count = self.requests.filter(
            status=ServiceRequest.Status.COMPLETED
        ).count()
        self.save(update_fields=["completed_jobs_count"])


# --- Services listed on a provider card (FR 3.6) ---
class ProviderService(models.Model):
    provider = models.ForeignKey(
        ServiceProvider, on_delete=models.CASCADE, related_name="services"
    )
    category = models.ForeignKey(
        ServiceCategory, on_delete=models.SET_NULL, null=True, blank=True
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.ImageField(upload_to="services/", blank=True)

    def __str__(self):
        return self.name


# --- Subscriptions and mock payments (FR 8.1 - 8.3) ---
class Subscription(models.Model):
    class Tier(models.TextChoices):
        STARTER = "STARTER", _("Starter")
        PRO = "PRO", _("Pro Partner")
        ELITE = "ELITE", _("Elite Master")

    class BillingCycle(models.TextChoices):
        MONTHLY = "MONTHLY", _("Monthly")
        ANNUAL = "ANNUAL", _("Annual")

    MONTHLY_PRICES = {"STARTER": 0, "PRO": 500, "ELITE": 1000}
    PORTFOLIO_LIMITS = {"STARTER": 3, "PRO": 15, "ELITE": None}
    SEARCH_RANK = {"STARTER": 1, "PRO": 2, "ELITE": 3}
    ANNUAL_DISCOUNT = Decimal("0.80")

    provider = models.OneToOneField(
        ServiceProvider, on_delete=models.CASCADE,
        related_name="subscription",
    )
    tier = models.CharField(
        max_length=10, choices=Tier.choices, default=Tier.STARTER
    )
    billing_cycle = models.CharField(
        max_length=10, choices=BillingCycle.choices,
        default=BillingCycle.MONTHLY,
    )
    search_rank = models.PositiveSmallIntegerField(default=1)
    commission_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=0
    )
    started_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.search_rank = self.SEARCH_RANK[self.tier]
        super().save(*args, **kwargs)

    @classmethod
    def price_for(cls, tier, billing_cycle):
        monthly = Decimal(cls.MONTHLY_PRICES[tier])
        if billing_cycle == cls.BillingCycle.ANNUAL:
            return (monthly * 12 * cls.ANNUAL_DISCOUNT).quantize(Decimal("1"))
        return monthly

    @property
    def price(self):
        return self.price_for(self.tier, self.billing_cycle)

    @property
    def portfolio_limit(self):
        return self.PORTFOLIO_LIMITS[self.tier]

    def __str__(self):
        return f"{self.provider} - {self.get_tier_display()}"


class Payment(models.Model):
    """A simulated payment. No card details are ever collected."""

    provider = models.ForeignKey(
        ServiceProvider, on_delete=models.CASCADE, related_name="payments"
    )
    tier = models.CharField(max_length=10, choices=Subscription.Tier.choices)
    billing_cycle = models.CharField(
        max_length=10, choices=Subscription.BillingCycle.choices
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reference = models.CharField(max_length=30)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class PlanChangeLog(models.Model):
    """Stores every plan or billing choice, by the provider or an admin."""

    provider = models.ForeignKey(
        ServiceProvider, on_delete=models.CASCADE, related_name="plan_logs"
    )
    changed_by = models.ForeignKey(
        USER, on_delete=models.SET_NULL, null=True, blank=True
    )
    old_tier = models.CharField(max_length=10, blank=True)
    new_tier = models.CharField(max_length=10)
    old_cycle = models.CharField(max_length=10, blank=True)
    new_cycle = models.CharField(max_length=10)
    old_commission = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    new_commission = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


# --- VERIFICATION_DOCUMENT and admin decisions (FR 7.1, 7.2) ---
class VerificationDocument(models.Model):
    class DocType(models.TextChoices):
        BRN = "BRN", _("Business Registration Document")
        NATIONAL_ID = "NATIONAL_ID", _("National ID")
        LICENSE = "LICENSE", _("License")
        CERTIFICATION = "CERTIFICATION", _("Certification")
        INSURANCE = "INSURANCE", _("Insurance")

    class Status(models.TextChoices):
        PENDING = "PENDING", _("Pending")
        APPROVED = "APPROVED", _("Approved")
        REJECTED = "REJECTED", _("Rejected")

    provider = models.ForeignKey(
        ServiceProvider, on_delete=models.CASCADE, related_name="documents"
    )
    doc_type = models.CharField(max_length=20, choices=DocType.choices)
    name = models.CharField(max_length=150, blank=True)
    file = models.FileField(upload_to="documents/")
    verification_status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return self.name or self.file.name


class VerificationLog(models.Model):
    class Action(models.TextChoices):
        STAGE = "STAGE", _("Stage changed")
        NOTE = "NOTE", _("Note added")
        APPROVE = "APPROVE", _("Approved")
        REJECT = "REJECT", _("Rejected")

    provider = models.ForeignKey(
        ServiceProvider, on_delete=models.CASCADE,
        related_name="verification_logs",
    )
    admin = models.ForeignKey(
        USER, on_delete=models.SET_NULL, null=True, blank=True
    )
    action = models.CharField(max_length=10, choices=Action.choices)
    stage = models.CharField(max_length=20, blank=True)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


# --- PORTFOLIO_ITEM (FR 3.5) ---
class PortfolioItem(models.Model):
    provider = models.ForeignKey(
        ServiceProvider, on_delete=models.CASCADE,
        related_name="portfolio_items",
    )
    title = models.CharField(max_length=120)
    client_name = models.CharField(max_length=80, blank=True)
    description = models.TextField(blank=True)
    completed_on = models.DateField(null=True, blank=True)
    photo = models.ImageField(upload_to="portfolio/", blank=True)
    blueprint = models.FileField(upload_to="portfolio/blueprints/", blank=True)
    technical_specs = models.FileField(
        upload_to="portfolio/specs/", blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-completed_on", "-created_at"]

    def __str__(self):
        return self.title


class PortfolioPhoto(models.Model):
    item = models.ForeignKey(
        PortfolioItem, on_delete=models.CASCADE, related_name="photos"
    )
    image = models.ImageField(upload_to="portfolio/")


class ProfileView(models.Model):
    """One row per profile visit, used for "Portfolio Views"."""

    provider = models.ForeignKey(
        ServiceProvider, on_delete=models.CASCADE, related_name="profile_views"
    )
    viewed_at = models.DateTimeField(auto_now_add=True)


# --- BOOKING_CALENDAR: schedule settings and blocked periods (FR 3.17) ---
class ScheduleSettings(models.Model):
    provider = models.OneToOneField(
        ServiceProvider, on_delete=models.CASCADE, related_name="schedule"
    )
    recurring_availability = models.BooleanField(default=True)
    range_start = models.DateField(null=True, blank=True)
    range_end = models.DateField(null=True, blank=True)
    services_offered = ArrayField(
        models.CharField(max_length=20, choices=JobType.choices),
        default=list, blank=True,
    )
    day_start = models.TimeField(default=datetime.time(9, 0))
    day_end = models.TimeField(default=datetime.time(18, 0))
    slot_minutes = models.PositiveSmallIntegerField(default=30)
    buffer_minutes = models.PositiveSmallIntegerField(default=30)
    updated_at = models.DateTimeField(auto_now=True)


class BlockedDate(models.Model):
    provider = models.ForeignKey(
        ServiceProvider, on_delete=models.CASCADE,
        related_name="blocked_dates",
    )
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["start_date"]


class BlockedTime(models.Model):
    provider = models.ForeignKey(
        ServiceProvider, on_delete=models.CASCADE,
        related_name="blocked_times",
    )
    label = models.CharField(max_length=60)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        ordering = ["start_time"]


# --- SERVICE_REQUEST (FR 2.8, 2.11, 3.9 - 3.13) ---
class ServiceRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", _("Pending Approval")
        ACCEPTED = "ACCEPTED", _("Scheduled")
        IN_PROGRESS = "IN_PROGRESS", _("In Progress")
        COMPLETED = "COMPLETED", _("Completed")
        DECLINED = "DECLINED", _("Declined")
        CANCELLED = "CANCELLED", _("Cancelled")

    class Urgency(models.TextChoices):
        NORMAL = "NORMAL", _("Normal")
        HIGH = "HIGH", _("High")

    class PayoutStatus(models.TextChoices):
        PENDING = "PENDING", _("Pending")
        PAID = "PAID", _("Paid")

    OPEN_STATUSES = [Status.PENDING, Status.ACCEPTED, Status.IN_PROGRESS]

    reference = models.CharField(max_length=20, unique=True, editable=False)
    client = models.ForeignKey(
        USER, on_delete=models.CASCADE, related_name="service_requests"
    )
    provider = models.ForeignKey(
        ServiceProvider, on_delete=models.CASCADE, related_name="requests"
    )
    category = models.ForeignKey(
        ServiceCategory, on_delete=models.SET_NULL, null=True, blank=True
    )
    job_type = models.CharField(
        max_length=20, choices=JobType.choices, default=JobType.OTHER
    )
    description = models.TextField()
    contact_name = models.CharField(max_length=120)
    contact_phone = models.CharField(max_length=20)
    contact_email = models.EmailField()
    location = models.CharField(max_length=200)
    preferred_date = models.DateField()
    urgency = models.CharField(
        max_length=10, choices=Urgency.choices, default=Urgency.NORMAL
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    final_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    payout_status = models.CharField(
        max_length=10, choices=PayoutStatus.choices,
        default=PayoutStatus.PENDING,
    )
    decline_reason = models.CharField(max_length=255, blank=True)
    admin_feedback = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.reference:
            number = ServiceRequest.objects.count() + 101
            while ServiceRequest.objects.filter(
                reference=f"TH-{number}"
            ).exists():
                number += 1
            self.reference = f"TH-{number}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.reference

    @property
    def is_open(self):
        return self.status in self.OPEN_STATUSES

    @property
    def client_contact_visible(self):
        """FR 3.13: contact details only after the provider accepts."""
        return self.status in [
            self.Status.ACCEPTED, self.Status.IN_PROGRESS,
            self.Status.COMPLETED,
        ]


class ServiceRequestPhoto(models.Model):
    request = models.ForeignKey(
        ServiceRequest, on_delete=models.CASCADE, related_name="photos"
    )
    image = models.ImageField(upload_to="requests/")


class RequestLog(models.Model):
    """Every change made to a request, by anyone, is stored here."""

    class Action(models.TextChoices):
        CREATED = "CREATED", _("Created")
        STATUS = "STATUS", _("Status changed")
        RESCHEDULE = "RESCHEDULE", _("Rescheduled")
        FEEDBACK = "FEEDBACK", _("Feedback recorded")
        REASSIGN = "REASSIGN", _("Reassigned")
        AMOUNT = "AMOUNT", _("Amount set")

    request = models.ForeignKey(
        ServiceRequest, on_delete=models.CASCADE, related_name="logs"
    )
    actor = models.ForeignKey(
        USER, on_delete=models.SET_NULL, null=True, blank=True
    )
    action = models.CharField(max_length=20, choices=Action.choices)
    old_value = models.CharField(max_length=120, blank=True)
    new_value = models.CharField(max_length=120, blank=True)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


# --- REVIEW (FR 2.9, 3.14, 6.1 - 6.4) ---
class Review(models.Model):
    request = models.OneToOneField(
        ServiceRequest, on_delete=models.CASCADE, related_name="review"
    )
    client = models.ForeignKey(
        USER, on_delete=models.CASCADE, related_name="reviews_written"
    )
    provider = models.ForeignKey(
        ServiceProvider, on_delete=models.CASCADE, related_name="reviews"
    )
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField(blank=True)
    provider_reply = models.TextField(blank=True)
    replied_at = models.DateTimeField(null=True, blank=True)
    is_removed = models.BooleanField(default=False)
    removed_reason = models.CharField(max_length=255, blank=True)
    removed_by = models.ForeignKey(
        USER, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="reviews_removed",
    )
    removed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.provider.recalculate_rating()


# --- WISHLIST_ITEM (FR 2.10) ---
class WishlistItem(models.Model):
    client = models.ForeignKey(
        USER, on_delete=models.CASCADE, related_name="wishlist_items"
    )
    provider = models.ForeignKey(
        ServiceProvider, on_delete=models.CASCADE, related_name="wishlisted_by"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["client", "provider"], name="unique_wishlist_item"
            ),
        ]


# --- Notifications (FR 3.3) ---
class Notification(models.Model):
    user = models.ForeignKey(
        USER, on_delete=models.CASCADE, related_name="notifications"
    )
    title = models.CharField(max_length=120)
    message = models.TextField()
    link = models.CharField(max_length=200, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


# --- Payouts (simulated) ---
class Payout(models.Model):
    class Status(models.TextChoices):
        REQUESTED = "REQUESTED", _("Requested")
        PAID = "PAID", _("Paid")

    provider = models.ForeignKey(
        ServiceProvider, on_delete=models.CASCADE, related_name="payouts"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PAID
    )
    bank_label = models.CharField(max_length=80, blank=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-requested_at"]


class BankDetailsLog(models.Model):
    """Every bank account change a provider saves."""

    provider = models.ForeignKey(
        ServiceProvider, on_delete=models.CASCADE, related_name="bank_logs"
    )
    bank_name = models.CharField(max_length=60)
    account_ending = models.CharField(max_length=4)
    created_at = models.DateTimeField(auto_now_add=True)


# --- Account status history (FR 7.4) ---
class AccountStatusLog(models.Model):
    user = models.ForeignKey(
        USER, on_delete=models.CASCADE, related_name="status_logs"
    )
    admin = models.ForeignKey(
        USER, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="status_changes_made",
    )
    old_status = models.CharField(max_length=20)
    new_status = models.CharField(max_length=20)
    reason = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
