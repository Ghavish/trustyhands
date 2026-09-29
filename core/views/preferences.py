"""Saves the light/dark theme and the interface language (FR 9.1)."""

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import redirect
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

ONE_YEAR = 60 * 60 * 24 * 365


@require_POST
def set_preferences(request):
    theme = request.POST.get("theme")
    language = request.POST.get("language")
    valid_languages = dict(settings.LANGUAGES)

    # Logged-in users: the choice is stored in MongoDB.
    user = request.user
    if user.is_authenticated:
        if theme in ("light", "dark"):
            user.theme = theme
        if language in valid_languages:
            user.preferred_language = language
        user.save(update_fields=["theme", "preferred_language"])

    # Everyone: the choice is also kept in a browser cookie, so guests
    # keep it until they register (it is then copied to their account).
    if request.headers.get("x-requested-with") == "fetch":
        response = JsonResponse({"ok": True})
    else:
        next_url = request.POST.get("next", "/")
        if not url_has_allowed_host_and_scheme(
            next_url, allowed_hosts={request.get_host()}
        ):
            next_url = "/"
        response = redirect(next_url)
    if theme in ("light", "dark"):
        response.set_cookie(
            settings.THEME_COOKIE_NAME, theme, max_age=ONE_YEAR
        )
    if language in valid_languages:
        response.set_cookie(
            settings.LANGUAGE_COOKIE_NAME, language, max_age=ONE_YEAR
        )
    return response
