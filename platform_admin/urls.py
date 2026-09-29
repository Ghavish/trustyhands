"""Admin screens, all under /dashboard-admin/."""

from django.urls import path

from platform_admin.views import (
    analytics, categories, review_moderation, service_requests,
    user_management, verification,
)

app_name = "dashboard"

urlpatterns = [
    # --- Somanshu ---
    path("", analytics.analytics_dashboard, name="analytics"),
    path(
        "verification/",
        verification.verification_queue,
        name="verification_queue",
    ),
    path(
        "verification/<object_id:pk>/",
        verification.verification_detail,
        name="verification_detail",
    ),
    path(
        "users/", user_management.user_management, name="user_management"
    ),
    path(
        "users/<object_id:pk>/",
        user_management.user_detail,
        name="user_detail",
    ),
    path(
        "requests/",
        service_requests.service_requests,
        name="service_requests",
    ),
    path(
        "requests/<object_id:pk>/",
        service_requests.request_detail,
        name="request_detail",
    ),
    path(
        "categories/",
        categories.category_management,
        name="category_management",
    ),
    # --- Yashmeeta ---
    path(
        "reviews/",
        review_moderation.review_moderation,
        name="review_moderation",
    ),
]
