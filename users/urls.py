from django.urls import path

from users.views import auth
from users.views.edit_profile import edit_profile

app_name = "users"

urlpatterns = [
    path("login/", auth.LoginView.as_view(), name="login"),
    path("logout/", auth.LogoutView.as_view(), name="logout"),
    path("register/", auth.register, name="register"),
    path(
        "password-reset/",
        auth.PasswordResetView.as_view(),
        name="password_reset",
    ),
    path(
        "password-reset/sent/",
        auth.PasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth.PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth.PasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
    path("profile/edit/", edit_profile, name="edit_profile"),
]
