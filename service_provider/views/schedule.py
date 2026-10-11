"""
Schedule Manager (Meer). FR 3.8 and 3.17: the provider's booking calendar,
working hours, blocked dates and blocked times. Every setting is saved.
"""

import datetime

from django import forms
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.views.decorators.http import require_POST

from core.choices import JobType
from core.decorators import provider_profile_required
from core.models import BlockedDate, BlockedTime, ScheduleSettings, ServiceRequest
from core.utils import month_grid, read_month, shift_month

Status = ServiceRequest.Status
BOOKED = [Status.ACCEPTED, Status.IN_PROGRESS]


# --- Forms ---
class SettingsForm(forms.ModelForm):
    services_offered = forms.MultipleChoiceField(
        label=gettext_lazy("Services Offered"),
        choices=JobType.choices,
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    class Meta:
        model = ScheduleSettings
        fields = [
            "recurring_availability", "range_start", "range_end",
            "services_offered", "day_start", "day_end", "slot_minutes",
            "buffer_minutes",
        ]
        labels = {
            "recurring_availability": gettext_lazy("Recurring Availability"),
            "range_start": gettext_lazy("From"),
            "range_end": gettext_lazy("To"),
            "day_start": gettext_lazy("Day starts"),
            "day_end": gettext_lazy("Day ends"),
            "slot_minutes": gettext_lazy("Slot (min)"),
            "buffer_minutes": gettext_lazy("Buffer (min)"),
        }
        widgets = {
            "range_start": forms.DateInput(attrs={"type": "date"}),
            "range_end": forms.DateInput(attrs={"type": "date"}),
            "day_start": forms.TimeInput(attrs={"type": "time"}),
            "day_end": forms.TimeInput(attrs={"type": "time"}),
        }


class BlockedDateForm(forms.ModelForm):
    class Meta:
        model = BlockedDate
        fields = ["start_date", "end_date", "reason"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }

    def clean(self):
        data = super().clean()
        if data.get("start_date") and data.get("end_date"):
            if data["end_date"] < data["start_date"]:
                raise forms.ValidationError(_("The end date is before the start."))
        return data


class BlockedTimeForm(forms.ModelForm):
    class Meta:
        model = BlockedTime
        fields = ["label", "start_time", "end_time"]
        widgets = {
            "start_time": forms.TimeInput(attrs={"type": "time"}),
            "end_time": forms.TimeInput(attrs={"type": "time"}),
        }


# --- Calculations for the stat cards ---
def minutes_between(start, end):
    return (end.hour * 60 + end.minute) - (start.hour * 60 + start.minute)


def slots_per_day(settings, blocked_times):
    working = minutes_between(settings.day_start, settings.day_end)
    for block in blocked_times:
        working -= max(0, minutes_between(block.start_time, block.end_time))
    step = settings.slot_minutes + settings.buffer_minutes
    return max(0, working // step) if step else 0


def is_blocked(day, blocked_dates):
    return any(b.start_date <= day <= b.end_date for b in blocked_dates)


def week_capacity(provider, settings, today):
    """Free slots and how full the current week (Sunday to Saturday) is."""
    blocked_dates = list(provider.blocked_dates.all())
    per_day = slots_per_day(settings, provider.blocked_times.all())
    week_start = today - datetime.timedelta(days=(today.weekday() + 1) % 7)
    week = [week_start + datetime.timedelta(days=n) for n in range(7)]
    open_days = [day for day in week if not is_blocked(day, blocked_dates)]
    if not settings.recurring_availability and settings.range_start:
        end = settings.range_end or settings.range_start
        open_days = [d for d in open_days if settings.range_start <= d <= end]
    total = per_day * len(open_days)
    booked = provider.requests.filter(
        status__in=BOOKED, preferred_date__range=(week[0], week[-1])
    ).count()
    percent = round(booked / total * 100) if total else 0
    return max(0, total - booked), min(percent, 100)


def chip_class(job):
    """Colour of a job on the calendar, matching the Figma legend."""
    if job.urgency == ServiceRequest.Urgency.HIGH:
        return "high"
    return {
        "PLUMBING": "plumbing", "REPAIRS": "plumbing",
        "INSTALLATION": "installation", "MAINTENANCE": "maintenance",
    }.get(job.job_type, "other")


# --- Views ---
@provider_profile_required
def schedule_manager(request):
    provider = request.provider
    settings = provider.schedule
    today = timezone.localdate()
    view = request.GET.get("view", "month")

    settings_form = SettingsForm(instance=settings)
    date_form = BlockedDateForm()
    time_form = BlockedTimeForm()
    action = request.POST.get("action")

    if request.method == "POST" and action == "settings":
        settings_form = SettingsForm(request.POST, instance=settings)
        if settings_form.is_valid():
            settings_form.save()
            messages.success(request, _("Schedule settings saved."))
            return redirect(request.get_full_path())
    elif request.method == "POST" and action == "block_date":
        date_form = BlockedDateForm(request.POST)
        if date_form.is_valid():
            blocked = date_form.save(commit=False)
            blocked.provider = provider
            blocked.save()
            messages.success(request, _("Dates blocked out."))
            return redirect(request.get_full_path())
    elif request.method == "POST" and action == "block_time":
        time_form = BlockedTimeForm(request.POST)
        if time_form.is_valid():
            blocked = time_form.save(commit=False)
            blocked.provider = provider
            blocked.save()
            messages.success(request, _("Time blocked out."))
            return redirect(request.get_full_path())

    # --- Calendar: month grid, one week, or one day ---
    year, month = read_month(request)
    weeks = month_grid(year, month)
    if view == "week":
        weeks = [w for w in weeks if today in w] or weeks[:1]
    days_shown = [day for week in weeks for day in week]
    jobs = provider.requests.filter(
        preferred_date__range=(days_shown[0], days_shown[-1]),
        status__in=BOOKED + [Status.PENDING, Status.COMPLETED],
    ).select_related("client")
    by_day = {}
    for job in jobs:
        job.chip = chip_class(job)
        by_day.setdefault(job.preferred_date, []).append(job)
    blocked_dates = list(provider.blocked_dates.all())
    calendar_weeks = [
        [
            {
                "date": day,
                "in_month": day.month == month,
                "jobs": by_day.get(day, []),
                "blocked": is_blocked(day, blocked_dates),
                "today": day == today,
            }
            for day in week
        ]
        for week in weeks
    ]

    free_slots, percent_full = week_capacity(provider, settings, today)
    client_counts = {}
    for client_id in provider.requests.values_list("client_id", flat=True):
        client_counts[client_id] = client_counts.get(client_id, 0) + 1
    conflicts = [
        job for job in provider.requests.filter(
            status__in=BOOKED, preferred_date__gte=today
        )
        if is_blocked(job.preferred_date, blocked_dates)
    ]

    context = {
        "view": view,
        "year": year,
        "month_date": datetime.date(year, month, 1),
        "prev": shift_month(year, month, -1),
        "next": shift_month(year, month, 1),
        "calendar_weeks": calendar_weeks,
        "day_jobs": by_day.get(today, []),
        "today": today,
        "confirmed_today": provider.requests.filter(
            status__in=BOOKED, preferred_date=today
        ).count(),
        "free_slots": free_slots,
        "percent_full": percent_full,
        "recurring_clients": sum(1 for n in client_counts.values() if n > 1),
        "conflicts": len(conflicts),
        "settings_form": settings_form,
        "date_form": date_form,
        "time_form": time_form,
        "blocked_dates": blocked_dates,
        "blocked_times": provider.blocked_times.all(),
    }
    return render(request, "service_provider/schedule.html", context)


@provider_profile_required
@require_POST
def delete_blocked_date(request, pk):
    get_object_or_404(BlockedDate, pk=pk, provider=request.provider).delete()
    messages.info(request, _("Blocked dates removed."))
    return redirect("provider:schedule_manager")


@provider_profile_required
@require_POST
def delete_blocked_time(request, pk):
    get_object_or_404(BlockedTime, pk=pk, provider=request.provider).delete()
    messages.info(request, _("Blocked time removed."))
    return redirect("provider:schedule_manager")
