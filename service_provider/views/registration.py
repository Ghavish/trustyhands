from django import forms
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from core.choices import District
from core.decorators import provider_required
from core.forms import MultipleImageField
from core.models import (
    PortfolioItem, PortfolioPhoto, ScheduleSettings, ServiceCategory,
    ServiceProvider, Subscription, VerificationDocument,
)
from core.utils import notify

YEARS = [(year, f"{year}+") for year in range(0, 41)]


class ProfileForm(forms.Form):
    full_name = forms.CharField(label=gettext_lazy("Your Full Name"), max_length=120)
    profession_title = forms.CharField(
        label=gettext_lazy("Profession and Title"), max_length=120
    )
    categories = forms.ModelMultipleChoiceField(
        label=gettext_lazy("Services you offer"),
        queryset=ServiceCategory.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple,
    )
    years_experience = forms.TypedChoiceField(
        label=gettext_lazy("Years Of Experience"), choices=YEARS, coerce=int
    )
    district = forms.ChoiceField(
        label=gettext_lazy("Primary Location"), choices=District.choices
    )
    bio = forms.CharField(
        label=gettext_lazy("About Me & Biography"),
        widget=forms.Textarea(attrs={
            "placeholder": gettext_lazy(
                "Briefly share your biography and expert statement here...."
            ),
        }),
    )
    document_type = forms.ChoiceField(
        label=gettext_lazy("Verification document"),
        choices=[
            (VerificationDocument.DocType.BRN,
             VerificationDocument.DocType.BRN.label),
            (VerificationDocument.DocType.NATIONAL_ID,
             VerificationDocument.DocType.NATIONAL_ID.label),
        ],
    )
    document = forms.FileField(
        label=gettext_lazy("Upload the document (PDF or picture)")
    )


class ProjectForm(forms.Form):
    title = forms.CharField(label=gettext_lazy("Project name"), max_length=120)
    blueprint = forms.FileField(
        label=gettext_lazy("Upload Project Blueprint"), required=False
    )
    technical_specs = forms.FileField(
        label=gettext_lazy("Add Technical Specs"), required=False
    )
    photos = MultipleImageField(
        label=gettext_lazy("Add Project Photos"), required=False, max_files=10
    )


ProjectFormSet = forms.formset_factory(
    ProjectForm, extra=0, min_num=1, validate_min=True
)


def save_profile(user, profile_form, project_formset):
    """Create every record for the new provider."""
    data = profile_form.cleaned_data
    provider = ServiceProvider.objects.create(
        user=user,
        business_name=data["full_name"],
        profession_title=data["profession_title"],
        years_experience=data["years_experience"],
        district=data["district"],
        areas_served=[data["district"]],
        bio=data["bio"],
        submitted_at=timezone.now(),
    )
    provider.categories.set(data["categories"])
    VerificationDocument.objects.create(
        provider=provider, doc_type=data["document_type"],
        name=data["document"].name, file=data["document"],
    )
    for project in project_formset.cleaned_data:
        if not project.get("title"):
            continue
        photos = project["photos"]
        item = PortfolioItem.objects.create(
            provider=provider,
            title=project["title"],
            blueprint=project.get("blueprint") or "",
            technical_specs=project.get("technical_specs") or "",
            photo=photos[0] if photos else "",
            completed_on=timezone.localdate(),
        )
        for photo in photos[1:]:
            PortfolioPhoto.objects.create(item=item, image=photo)
    Subscription.objects.create(provider=provider)
    ScheduleSettings.objects.create(provider=provider)
    return provider


@provider_required
def portfolio_hub(request):
    if hasattr(request.user, "provider_profile"):
        return redirect("provider:active_jobs")

    user = request.user
    profile_form = ProfileForm(
        request.POST or None, request.FILES or None,
        initial={"full_name": user.display_name, "district": user.district},
    )
    project_formset = ProjectFormSet(
        request.POST or None, request.FILES or None, prefix="projects"
    )
    if (
        request.method == "POST"
        and profile_form.is_valid()
        and project_formset.is_valid()
    ):
        provider = save_profile(user, profile_form, project_formset)
        admins = get_user_model().objects.filter(
            Q(role="ADMIN") | Q(is_superuser=True)
        )
        for admin in admins:
            notify(
                admin, _("New provider to verify"),
                _("%(name)s submitted a profile for verification.")
                % {"name": provider.business_name},
                reverse("dashboard:verification_queue"),
            )
        messages.success(
            request, _("Profile submitted! Now choose your plan.")
        )
        return redirect("provider:choose_plan")

    context = {
        "form": profile_form,
        "projects": project_formset,
    }
    return render(request, "service_provider/registration.html", context)