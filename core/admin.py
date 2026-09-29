"""Every TrustyHands collection is visible at /admin/ for debugging."""

from django.contrib import admin

from core import models

for model in [
    models.ServiceCategory, models.ServiceProvider, models.ProviderService,
    models.Subscription, models.Payment, models.PlanChangeLog,
    models.VerificationDocument, models.VerificationLog,
    models.PortfolioItem, models.PortfolioPhoto, models.ProfileView,
    models.ScheduleSettings, models.BlockedDate, models.BlockedTime,
    models.ServiceRequest, models.ServiceRequestPhoto, models.RequestLog,
    models.Review, models.WishlistItem, models.Notification, models.Payout,
    models.BankDetailsLog, models.AccountStatusLog,
]:
    admin.site.register(model)
