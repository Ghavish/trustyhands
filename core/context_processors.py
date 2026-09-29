"""Values available in every template."""

from django.conf import settings

from core.models import Notification


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

    return {
        "current_theme": theme,
        "unread_notifications": unread,
        "generic_shell": generic_shell,
    }
