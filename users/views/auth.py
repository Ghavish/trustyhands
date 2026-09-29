"""Login, logout, registration and password reset (FR 1.1 - 1.4, 1.6)."""

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils.translation import gettext as _

from users.forms import LoginForm, RegisterForm


class LoginView(auth_views.LoginView):
    template_name = "users/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True


class LogoutView(auth_views.LogoutView):
    pass


def register(request):
    if request.user.is_authenticated:
        return redirect("core:after_login")
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save(commit=False)
        # Copy the choices a guest made before registering.
        theme = request.COOKIES.get(settings.THEME_COOKIE_NAME)
        language = request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME)
        if theme in ("light", "dark"):
            user.theme = theme
        if language in dict(settings.LANGUAGES):
            user.preferred_language = language
        user.save()
        login(request, user, backend=settings.AUTHENTICATION_BACKENDS[0])
        messages.success(request, _("Welcome to TrustyHands!"))
        return redirect("core:after_login")
    return render(request, "users/register.html", {"form": form})


# --- Password reset by email (FR 1.4) ---
class PasswordResetView(auth_views.PasswordResetView):
    template_name = "users/password_reset_form.html"
    email_template_name = "users/password_reset_email.txt"
    subject_template_name = "users/password_reset_subject.txt"
    success_url = reverse_lazy("users:password_reset_done")


class PasswordResetDoneView(auth_views.PasswordResetDoneView):
    template_name = "users/password_reset_done.html"


class PasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    template_name = "users/password_reset_confirm.html"
    success_url = reverse_lazy("users:password_reset_complete")


class PasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    template_name = "users/password_reset_complete.html"
