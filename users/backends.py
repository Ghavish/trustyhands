"""Lets users log in with their email address or phone number (FR 1.2)."""

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

class EmailOrPhoneBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None
        user_model = get_user_model()
        identifier = username.strip()
        user = user_model.objects.filter(
            Q(email__iexact=identifier) | Q(phone=identifier)
        ).first()
        if user is None:
            # Run the hasher anyway so timing does not reveal missing users.
            user_model().set_password(password)
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
