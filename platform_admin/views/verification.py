"""
Verification Queue (Somanshu). FR 7.1, 7.2 and 3.3.
Admins move a provider through the checks, add notes, and approve or
reject (a reason is required to reject). Every decision is logged.
"""

from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _

from core.decorators import admin_required
from core.models import ServiceProvider, VerificationLog
from core.utils import notify

Log = VerificationLog.Action
Stage = ServiceProvider.VerificationStage
Status = ServiceProvider.VerificationStatus


def handle_decision(request, provider):
    """Apply one admin action from a POST form. Returns True if saved."""
    action = request.POST.get("action")
    note = request.POST.get("note", "").strip()
    admin = request.user

    if action == "stage":
        stage = request.POST.get("stage")
        if stage not in Stage.values:
            return False
        provider.verification_stage = stage
        provider.save(update_fields=["verification_stage"])
        VerificationLog.objects.create(
            provider=provider, admin=admin, action=Log.STAGE, stage=stage
        )
        messages.success(request, _("Verification stage updated."))
        return True

    if action == "note" and note:
        VerificationLog.objects.create(
            provider=provider, admin=admin, action=Log.NOTE, note=note,
            stage=provider.verification_stage,
        )
        if request.POST.get("ask_provider"):
            provider.verification_status = Status.MORE_INFO
            provider.save(update_fields=["verification_status"])
            notify(
                provider.user, _("More information needed"), note,
                reverse("users:edit_profile"),
            )
        messages.success(request, _("Note saved."))
        return True

    if action == "approve":
        provider.verification_status = Status.APPROVED
        provider.verified_at = timezone.now()
        provider.rejection_reason = ""
        provider.save()
        provider.documents.update(verification_status="APPROVED")
        VerificationLog.objects.create(
            provider=provider, admin=admin, action=Log.APPROVE,
            stage=provider.verification_stage, note=note,
        )
        notify(
            provider.user, _("Profile verified"),
            _("Your profile was approved. Clients can now find you."),
            reverse("provider:active_jobs"),
        )
        messages.success(
            request, _("%(name)s is approved.") % {"name": provider.business_name}
        )
        return True

    if action == "reject":
        if not note:
            messages.error(request, _("A reason is required to reject."))
            return False
        provider.verification_status = Status.REJECTED
        provider.rejection_reason = note
        provider.save()
        VerificationLog.objects.create(
            provider=provider, admin=admin, action=Log.REJECT,
            stage=provider.verification_stage, note=note,
        )
        notify(
            provider.user, _("Profile not approved"),
            _("Reason: %(reason)s") % {"reason": note},
            reverse("users:edit_profile"),
        )
        messages.success(request, _("The provider was rejected."))
        return True
    return False


@admin_required
def verification_queue(request):
    if request.method == "POST":
        provider = get_object_or_404(
            ServiceProvider, pk=request.POST.get("provider_id")
        )
        handle_decision(request, provider)
        return redirect(request.get_full_path())

    show = request.GET.get("show", "open")
    providers = ServiceProvider.objects.select_related("user").order_by(
        "-submitted_at"
    )
    if show == "open":
        providers = providers.filter(
            verification_status__in=[Status.PENDING, Status.MORE_INFO]
        )
    elif show in Status.values:
        providers = providers.filter(verification_status=show)

    page = Paginator(providers, 7).get_page(request.GET.get("page"))
    for provider in page:
        provider.category_names = ", ".join(
            provider.categories.values_list("name", flat=True)
        )
    context = {
        "page_obj": page,
        "show": show,
        "statuses": Status.choices,
        "stages": Stage.choices,
    }
    return render(request, "platform_admin/verification_queue.html", context)


@admin_required
def verification_detail(request, pk):
    provider = get_object_or_404(
        ServiceProvider.objects.select_related("user"), pk=pk
    )
    if request.method == "POST":
        handle_decision(request, provider)
        return redirect("dashboard:verification_detail", pk=provider.pk)
    context = {
        "provider": provider,
        "documents": provider.documents.all(),
        "logs": provider.verification_logs.select_related("admin"),
        "stages": Stage.choices,
    }
    return render(request, "platform_admin/verification_detail.html", context)
