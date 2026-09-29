"""Login and registration forms."""

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.utils.translation import gettext_lazy as _

from core.choices import District

User = get_user_model()


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label=_("Email or phone number"),
        widget=forms.TextInput(attrs={"autofocus": True}),
    )

    error_messages = {
        "invalid_login": _(
            "Wrong email/phone or password. Please try again."
        ),
        "inactive": _("This account is suspended or deactivated."),
    }


class RegisterForm(UserCreationForm):
    """FR 1.1: a guest registers as a Client or a Service Provider."""

    role = forms.ChoiceField(
        label=_("I want to"),
        choices=[
            (User.Role.CLIENT, _("Hire a professional (Client)")),
            (User.Role.PROVIDER, _("Offer my services (Service Provider)")),
        ],
        widget=forms.RadioSelect,
        initial=User.Role.CLIENT,
    )
    first_name = forms.CharField(label=_("First name"), max_length=150)
    last_name = forms.CharField(label=_("Last name"), max_length=150)
    email = forms.EmailField(label=_("Email address"))
    phone = forms.CharField(label=_("Phone number"), max_length=20)
    district = forms.ChoiceField(
        label=_("District"), choices=District.choices
    )

    class Meta:
        model = User
        fields = [
            "role", "first_name", "last_name", "email", "phone", "district",
        ]

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                _("An account with this email already exists.")
            )
        return email

    def clean_phone(self):
        phone = self.cleaned_data["phone"].strip()
        if User.objects.filter(phone=phone).exists():
            raise forms.ValidationError(
                _("An account with this phone number already exists.")
            )
        return phone

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = user.email
        user.role = self.cleaned_data["role"]
        if commit:
            user.save()
        return user
