"""
Portfolio Editor (Muneesh). FR 3.4 and 3.5.
Projects are limited by the subscription: 3 Starter, 15 Pro, unlimited Elite.
"""

import datetime

from django import forms
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.views.decorators.http import require_POST

from core.decorators import provider_profile_required
from core.models import PortfolioItem, ServiceProvider, VerificationDocument
from core.utils import day_end, day_start, parse_date_range


class ProjectForm(forms.ModelForm):
    class Meta:
        model = PortfolioItem
        fields = [
            "title", "client_name", "completed_on", "photo", "description",
            "blueprint", "technical_specs",
        ]
        widgets = {
            "completed_on": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 3}),
        }


class DetailsForm(forms.ModelForm):
    class Meta:
        model = ServiceProvider
        fields = ["main_specializations", "bio"]
        labels = {
            "main_specializations": gettext_lazy(
                "Main Service Specialization (one per line)"
            ),
            "bio": gettext_lazy("Professional Biography"),
        }
        widgets = {
            "main_specializations": forms.Textarea(attrs={"rows": 4}),
            "bio": forms.Textarea(attrs={"rows": 6}),
        }


class CertificationForm(forms.ModelForm):
    class Meta:
        model = VerificationDocument
        fields = ["doc_type", "name", "file"]
        labels = {"name": gettext_lazy("Name")}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["doc_type"].choices = [
            ("LICENSE", VerificationDocument.DocType.LICENSE.label),
            ("CERTIFICATION", VerificationDocument.DocType.CERTIFICATION.label),
            ("INSURANCE", VerificationDocument.DocType.INSURANCE.label),
        ]


def view_trend(provider, start, end):
    """Profile views per day, for the "Portfolio Views" sparkline."""
    counts = {}
    for view in provider.profile_views.filter(
        viewed_at__range=(day_start(start), day_end(end))
    ):
        day = timezone.localtime(view.viewed_at).date()
        counts[day] = counts.get(day, 0) + 1
    return [
        counts.get(start + datetime.timedelta(days=offset), 0)
        for offset in range((end - start).days + 1)
    ]


@provider_profile_required
def portfolio_editor(request):
    provider = request.provider
    limit = provider.subscription.portfolio_limit
    items = provider.portfolio_items.all()
    editing = None
    if request.GET.get("edit"):
        editing = get_object_or_404(
            PortfolioItem, pk=request.GET["edit"], provider=provider
        )

    project_form = ProjectForm(instance=editing)
    details_form = DetailsForm(instance=provider)
    certification_form = CertificationForm()
    action = request.POST.get("action")

    if request.method == "POST" and action == "save_project":
        project_form = ProjectForm(request.POST, request.FILES, instance=editing)
        if editing is None and limit is not None and items.count() >= limit:
            messages.error(
                request,
                _("Your plan allows %(limit)s projects. Upgrade to add more.")
                % {"limit": limit},
            )
        elif project_form.is_valid():
            project = project_form.save(commit=False)
            project.provider = provider
            project.save()
            messages.success(request, _("Project saved."))
            return redirect("provider:portfolio_editor")

    elif request.method == "POST" and action == "save_details":
        details_form = DetailsForm(request.POST, instance=provider)
        if details_form.is_valid():
            details_form.save()
            messages.success(request, _("Portfolio details saved."))
            return redirect("provider:portfolio_editor")

    elif request.method == "POST" and action == "add_certification":
        certification_form = CertificationForm(request.POST, request.FILES)
        if certification_form.is_valid():
            document = certification_form.save(commit=False)
            document.provider = provider
            document.save()
            messages.success(
                request, _("Certification added. An admin will check it.")
            )
            return redirect("provider:portfolio_editor")

    start, end = parse_date_range(request)
    certifications = provider.documents.filter(
        doc_type__in=["LICENSE", "CERTIFICATION", "INSURANCE"]
    )
    context = {
        "range_start": start,
        "range_end": end,
        "items": items,
        "limit": limit,
        "can_add": limit is None or items.count() < limit,
        "editing": editing,
        "project_form": project_form,
        "details_form": details_form,
        "certification_form": certification_form,
        "certifications": certifications,
        "active_certifications": certifications.filter(
            verification_status="APPROVED"
        ).count(),
        "view_count": provider.profile_views.count(),
        "views": view_trend(provider, start, end),
    }
    return render(request, "service_provider/portfolio_editor.html", context)


@provider_profile_required
@require_POST
def delete_project(request, pk):
    project = get_object_or_404(PortfolioItem, pk=pk, provider=request.provider)
    project.delete()
    messages.info(request, _("Project deleted."))
    return redirect("provider:portfolio_editor")