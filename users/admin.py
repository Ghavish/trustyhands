from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from users.models import User


@admin.register(User)
class TrustyHandsUserAdmin(UserAdmin):
    list_display = ["email", "first_name", "last_name", "role", "account_status"]
    list_filter = ["role", "account_status"]
    fieldsets = UserAdmin.fieldsets + (
        (
            "TrustyHands",
            {
                "fields": (
                    "role", "phone", "address", "district",
                    "profile_picture", "preferred_language", "theme",
                    "account_status", "status_reason",
                )
            },
        ),
    )
