"""
Active Jobs & Requests (Muneesh): the provider dashboard.
FR 3.9 view requests, 3.10 accept, 3.11 decline, 3.12 complete,
3.13 client contact only after accepting.
"""

import datetime
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from core.decorators import provider_profile_required
from core.models import RequestLog, ServiceRequest
from core.utils import notify, parse_date_range, redirect_back

Status = ServiceRequest.Status


def running_total(jobs, start, end):
    """
    Jobs added up day by day over the range, for the small trend lines.
    Example: 0, 1, 1, 3, 4 ... (the line only goes up).
    """
    counts = {}
    for job in jobs:
        counts[job.preferred_date] = counts.get(job.preferred_date, 0) + 1
    totals, running = [], 0
    for offset in range((end - start).days + 1):
        running += counts.get(start + datetime.timedelta(days=offset), 0)
        totals.append(running)
    return totals


@provider_profile_required
def active_jobs(request):
    provider = request.provider
    start, end = parse_date_range(request)
    today = timezone.localdate()
    jobs = provider.requests.select_related("client", "category")

    current = jobs.filter(
        status__in=[Status.ACCEPTED, Status.IN_PROGRESS],
        preferred_date__range=(start, end),
    ).order_by("preferred_date")
    # "HIGH" sorts before "NORMAL", so urgent requests come first.
    queue = jobs.filter(status=Status.PENDING).order_by("urgency", "created_at")
    upcoming = jobs.filter(
        status=Status.ACCEPTED, preferred_date__gte=today
    ).order_by("preferred_date")
    in_range = list(jobs.filter(preferred_date__range=(start, end)))

    context = {
        "range_start": start,
        "range_end": end,
        "active_count": jobs.filter(status=Status.IN_PROGRESS).count(),
        "pending_count": queue.count(),
        "upcoming_count": upcoming.count(),
        "upcoming": upcoming[:3],
        "rating": provider.average_rating,
        "current": current,
        "queue": queue,
        "active_trend": running_total(
            [j for j in in_range if j.status != Status.PENDING], start, end
        ),
        "pending_trend": running_total(
            [j for j in in_range if j.status == Status.PENDING], start, end
        ),
    }
    return render(request, "service_provider/active_jobs.html", context)


@provider_profile_required
def job_detail(request, pk):
    job = get_object_or_404(
        ServiceRequest.objects.select_related("client", "category"),
        pk=pk, provider=request.provider,
    )
    context = {"job": job, "logs": job.logs.select_related("actor")}
    return render(request, "service_provider/job_detail.html", context)


@provider_profile_required
@require_POST
def update_job(request, pk):
    job = get_object_or_404(ServiceRequest, pk=pk, provider=request.provider)
    action = request.POST.get("action")
    old_status = job.status
    now = timezone.now()

    # Which move is allowed from which status.
    moves = {
        "accept": (Status.PENDING, Status.ACCEPTED),
        "decline": (Status.PENDING, Status.DECLINED),
        "onsite": (Status.ACCEPTED, Status.IN_PROGRESS),
        "complete": (Status.IN_PROGRESS, Status.COMPLETED),
    }
    if action not in moves or job.status != moves[action][0]:
        messages.error(request, _("That action is not possible right now."))
        return redirect("provider:active_jobs")

    if action == "complete":
        # The provider enters the final amount when completing (business rule).
        try:
            amount = Decimal(request.POST.get("final_amount", ""))
        except InvalidOperation:
            amount = Decimal("-1")
        if amount < 0:
            messages.error(request, _("Please enter the final amount in MUR."))
            return redirect("provider:job_detail", pk=job.pk)
        job.final_amount = amount
        job.completed_at = now
        RequestLog.objects.create(
            request=job, actor=request.user, action=RequestLog.Action.AMOUNT,
            new_value=str(amount),
        )
    if action == "accept":
        job.accepted_at = now
    if action == "decline":
        job.decline_reason = request.POST.get("reason", "")[:255]

    job.status = moves[action][1]
    job.save()
    RequestLog.objects.create(
        request=job, actor=request.user, action=RequestLog.Action.STATUS,
        old_value=old_status, new_value=job.status,
        note=job.decline_reason if action == "decline" else "",
    )
    if action == "complete":
        request.provider.recalculate_completed_jobs()

    notify(
        job.client, _("Update on request %(ref)s") % {"ref": job.reference},
        _("Your request is now: %(status)s.")
        % {"status": job.get_status_display()},
        reverse("client:my_requests"),
    )
    messages.success(
        request,
        _("%(ref)s is now %(status)s.")
        % {"ref": job.reference, "status": job.get_status_display()},
    )
    return redirect_back(request, "provider:active_jobs")