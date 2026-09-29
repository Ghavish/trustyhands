"""Decorators that keep each role inside its own screens."""

from functools import wraps

from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import redirect
from django.utils.translation import gettext as _


def role_required(*roles):
    """
    Allow a view only for users whose role is in "roles".
    Guests are sent to the login page and come back afterwards.
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            if request.user.role not in roles:
                messages.error(
                    request, _("You do not have access to that page.")
                )
                return redirect("core:home")
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


client_required = role_required("CLIENT")
provider_required = role_required("PROVIDER")
admin_required = role_required("ADMIN")


def provider_profile_required(view_func):
    """
    For provider screens. Makes sure the provider finished the Portfolio
    Hub first, then puts their profile on "request.provider".
    """

    @wraps(view_func)
    @provider_required
    def wrapper(request, *args, **kwargs):
        provider = getattr(request.user, "provider_profile", None)
        if provider is None:
            messages.info(
                request, _("Please complete your professional profile first.")
            )
            return redirect("provider:registration")
        request.provider = provider
        return view_func(request, *args, **kwargs)

    return wrapper
