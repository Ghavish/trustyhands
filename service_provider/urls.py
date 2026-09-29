"""Service provider screens, all under /provider/."""

from django.urls import path

from service_provider.views import (
    active_jobs, earnings, landing, notifications, portfolio,
    registration, reviews, schedule, subscription,
)

app_name = "provider"

urlpatterns = [
    # --- Yashmeeta ---
    path("", landing.provider_landing, name="landing"),
    path("join/", registration.portfolio_hub, name="registration"),
    path("plan/", subscription.choose_plan, name="choose_plan"),
    path("plan/checkout/", subscription.checkout, name="checkout"),
    path(
        "notifications/", notifications.notifications, name="notifications"
    ),
    path(
        "notifications/read-all/",
        notifications.mark_all_read,
        name="mark_all_read",
    ),
    # --- Muneesh ---
    path("dashboard/", active_jobs.active_jobs, name="active_jobs"),
    path("jobs/<object_id:pk>/", active_jobs.job_detail, name="job_detail"),
    path(
        "jobs/<object_id:pk>/update/",
        active_jobs.update_job,
        name="job_update",
    ),
    path("portfolio/", portfolio.portfolio_editor, name="portfolio_editor"),
    path(
        "portfolio/<object_id:pk>/delete/",
        portfolio.delete_project,
        name="portfolio_delete",
    ),
    path("reviews/", reviews.provider_reviews, name="provider_reviews"),
    path(
        "reviews/<object_id:pk>/reply/",
        reviews.reply_review,
        name="review_reply",
    ),
    # --- Meer ---
    path("schedule/", schedule.schedule_manager, name="schedule_manager"),
    path(
        "schedule/blocked-date/<object_id:pk>/delete/",
        schedule.delete_blocked_date,
        name="schedule_delete_date",
    ),
    path(
        "schedule/blocked-time/<object_id:pk>/delete/",
        schedule.delete_blocked_time,
        name="schedule_delete_time",
    ),
    path("earnings/", earnings.earnings_overview, name="earnings_overview"),
    path(
        "earnings/invoice/<object_id:pk>/",
        earnings.invoice,
        name="earnings_invoice",
    ),
]
