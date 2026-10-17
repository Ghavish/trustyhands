"""Values available in every template."""

from django.conf import settings
from django.urls import reverse

from core.models import Notification

# The two landing pages are where people start, so they have no Back
# button. Every other screen, including Services and the sidebar
# screens, gets one.
HOME_VIEWS = {
    "core:home",
    "provider:landing",
}

# Sub-pages that already draw their own "Back" button in the page header.
OWN_BACK_BUTTON_VIEWS = {
    "provider:job_detail",
    "provider:checkout",
    "dashboard:request_detail",
    "dashboard:user_detail",
    "dashboard:verification_detail",
    "users:password_reset_done",
}


def back_fallback_url(user):
    """Where Back goes when there is no previous page on our site."""
    if user.is_authenticated and user.is_platform_admin:
        return reverse("dashboard:analytics")
    if user.is_authenticated and user.is_provider:
        return reverse("provider:active_jobs")
    return reverse("core:home")


def site_context(request):
    user = request.user
    if user.is_authenticated:
        theme = user.theme
        unread = Notification.objects.filter(user=user, is_read=False).count()
    else:
        theme = request.COOKIES.get(settings.THEME_COOKIE_NAME, "light")
        unread = 0
    if theme not in ("light", "dark"):
        theme = "light"

    # Screens built on the generic layout sit inside the right shell:
    # providers and admins get the sidebar, everyone else the navbar.
    if user.is_authenticated and (user.is_provider or user.is_platform_admin):
        generic_shell = "layouts/dashboard.html"
    else:
        generic_shell = "layouts/public.html"

    match = getattr(request, "resolver_match", None)
    view_name = match.view_name if match else ""
    show_back = bool(view_name) and view_name not in (
        HOME_VIEWS | OWN_BACK_BUTTON_VIEWS
    )

    return {
        "current_theme": theme,
        "unread_notifications": unread,
        "generic_shell": generic_shell,
        "show_back": show_back,
        "back_fallback": back_fallback_url(user),
    }
