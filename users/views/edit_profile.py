"""
Edit Profile (Khushi). One screen for clients and providers.
Clients: FR 1.5 / 2.1.  Providers also: FR 3.4, 3.6, 3.7, 3.8.
"""
from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from core.choices import District
from core.models import ProviderService, ServiceCategory, ServiceProvider
from users.models import User

# --- Forms --
class AccountForm(forms.ModelForm):
    """Fields every user has."""

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "phone",
            "address",
            "district",
            "profile_picture",
            "preferred_language",
            "theme",
        ]

    def clean_phone(self):
        phone = self.cleaned_data["phone"].strip()
        taken = User.objects.filter(phone=phone).exclude(pk=self.instance.pk)
        if phone and taken.exists():
            raise forms.ValidationError(
                _("Another account already uses this phone number.")
            )
        return phone

class ProviderDetailsForm(forms.ModelForm):
    """Extra fields for service providers."""

    categories = forms.ModelMultipleChoiceField(
        label=gettext_lazy("Service categories"),
        queryset=ServiceCategory.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple,
    )
    areas_served = forms.MultipleChoiceField(
        label=gettext_lazy("Areas served"),
        choices=District.choices,
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )
    class Meta:
        model = ServiceProvider
        fields = [
            "business_name", "profession_title", "availability", "town",
            "district", "areas_served", "years_experience", "client_type",
            "project_scale", "categories", "cover_photo", "bio",
            "specialty_areas", "common_issues", "service_requirements",
            "process_notes",
        ]
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 4}),
            "specialty_areas": forms.Textarea(attrs={"rows": 3}),
            "common_issues": forms.Textarea(attrs={"rows": 3}),
            "service_requirements": forms.Textarea(attrs={"rows": 2}),
            "process_notes": forms.Textarea(attrs={"rows": 2}),
        }
 
 
class ServiceForm(forms.ModelForm):
    """One service shown on the provider card (FR 3.6)."""
 
    class Meta:
        model = ProviderService
        fields = ["name", "category", "description", "icon"]
        widgets = {"description": forms.Textarea(attrs={"rows": 2})}
  
# --- View --
@login_required
def edit_profile(request):
    user = request.user
    provider = getattr(user, "provider_profile", None)
    action = request.POST.get("action", "profile")
 
    account_form = AccountForm(instance=user)
    details_form = ProviderDetailsForm(instance=provider) if provider else None
    service_form = ServiceForm() if provider else None
 
    if request.method == "POST" and action == "profile":
        account_form = AccountForm(request.POST, request.FILES, instance=user)
        if provider:
            details_form = ProviderDetailsForm(
                request.POST, request.FILES, instance=provider
            )
        forms_ok = account_form.is_valid() and (
            details_form is None or details_form.is_valid()
        )
        if forms_ok:
            account_form.save()
            if details_form:
                details_form.save()
            messages.success(request, _("Your profile has been saved."))
            return redirect("users:edit_profile")
 
    elif request.method == "POST" and action == "add_service" and provider:
        service_form = ServiceForm(request.POST, request.FILES)
        if service_form.is_valid():
            service = service_form.save(commit=False)
            service.provider = provider
            service.save()
            messages.success(request, _("Service added."))
            return redirect("users:edit_profile")
 
    elif request.method == "POST" and action == "delete_service" and provider:
        service = get_object_or_404(
            ProviderService, pk=request.POST.get("service_id"),
            provider=provider,
        )
        service.delete()
        messages.info(request, _("Service removed."))
        return redirect("users:edit_profile")
 
    context = {
        "account_form": account_form,
        "details_form": details_form,
        "service_form": service_form,
        "services": provider.services.all() if provider else [],
    }
    return render(request, "users/edit_profile.html", context)