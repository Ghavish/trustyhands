"""
Service Requests (Somanshu). End-to-end view of every request.
Admins can reschedule, record feedback and reassign declined requests.
Every change is written to RequestLog.
"""

import datetime

from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _

from core.decorators import admin_required
from core.models import RequestLog, ServiceProvider, ServiceRequest
from core.utils import notify

Status = ServiceRequest.Status


@admin_required
def service_requests(request):
    status = request.GET.get("status", "")
    jobs = ServiceRequest.objects.select_related(
        "client", "provider", "provider__user", "category"
    )
    if status in Status.values:
        jobs = jobs.filter(status=status)
    context = {
        "page_obj": Paginator(jobs, 7).get_page(request.GET.get("page")),
        "status": status,
        "statuses": Status.choices,
    }
    return render(request, "platform_admin/service_requests.html", context)


@admin_required
def request_detail(request, pk):
    job = get_object_or_404(
        ServiceRequest.objects.select_related("client", "provider"), pk=pk
    )
    action = request.POST.get("action")

    if request.method == "POST" and action == "reschedule":
        try:
            new_date = datetime.date.fromisoformat(request.POST.get("date", ""))
        except ValueError:
            messages.error(request, _("Please pick a valid date."))
            return redirect("dashboard:request_detail", pk=job.pk)
        RequestLog.objects.create(
            request=job, actor=request.user, action=RequestLog.Action.RESCHEDULE,
            old_value=job.preferred_date.isoformat(),
            new_value=new_date.isoformat(),
        )
        job.preferred_date = new_date
        job.save(update_fields=["preferred_date", "updated_at"])
        for person in (job.client, job.provider.user):
            notify(
                person, _("Request %(ref)s rescheduled") % {"ref": job.reference},
                _("New date: %(date)s") % {"date": new_date.strftime("%d %b %Y")},
            )
        messages.success(request, _("The request was rescheduled."))

    elif request.method == "POST" and action == "feedback":
        feedback = request.POST.get("feedback", "").strip()
        if feedback:
            job.admin_feedback = feedback
            job.save(update_fields=["admin_feedback", "updated_at"])
            RequestLog.objects.create(
                request=job, actor=request.user,
                action=RequestLog.Action.FEEDBACK, note=feedback,
            )
            messages.success(request, _("Feedback recorded."))

    elif request.method == "POST" and action == "reassign":
        new_provider = get_object_or_404(
            ServiceProvider, pk=request.POST.get("provider_id"),
            verification_status="APPROVED",
        )
        if job.status != Status.DECLINED:
            messages.error(request, _("Only declined requests can be reassigned."))
        else:
            RequestLog.objects.create(
                request=job, actor=request.user,
                action=RequestLog.Action.REASSIGN,
                old_value=job.provider.business_name,
                new_value=new_provider.business_name,
            )
            job.provider = new_provider
            job.status = Status.PENDING
            job.decline_reason = ""
            job.save()
            notify(
                new_provider.user, _("New job request"),
                _("TrustyHands assigned request %(ref)s to you.")
                % {"ref": job.reference},
                reverse("provider:active_jobs"),
            )
            notify(
                job.client, _("Request %(ref)s reassigned") % {"ref": job.reference},
                _("%(name)s will now handle your request.")
                % {"name": new_provider.business_name},
            )
            messages.success(request, _("The request was reassigned."))

    if request.method == "POST":
        return redirect("dashboard:request_detail", pk=job.pk)

    candidates = ServiceProvider.objects.filter(
        verification_status="APPROVED"
    ).exclude(pk=job.provider_id)
    if job.category_id:
        candidates = candidates.filter(categories=job.category_id)
    context = {
        "job": job,
        "logs": job.logs.select_related("actor"),
        "candidates": candidates,
    }
    return render(request, "platform_admin/request_detail.html", context)
