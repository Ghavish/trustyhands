"""The long scrolling landing page (hero, experts, join and footer)."""

from django.shortcuts import redirect, render

from core.models import ServiceCategory


def landing_context(show_dashboard_button=False):
    """Shared by the client landing page and the provider landing page."""
    return {
        "categories": ServiceCategory.objects.filter(is_active=True),
        "show_dashboard_button": show_dashboard_button,
        "on_landing": True,
    }


def client_landing(request):
    return render(request, "core/landing.html", landing_context())


def after_login(request):
    """Send each role to its own starting page after logging in."""
    user = request.user
    if not user.is_authenticated:
        return redirect("core:home")
    if user.is_platform_admin:
        return redirect("dashboard:analytics")
    if user.is_provider:
        if not hasattr(user, "provider_profile"):
            return redirect("provider:registration")
        return redirect("provider:landing")
    return redirect("core:home")
