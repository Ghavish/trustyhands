"""Small helpers shared by several screens."""

import calendar
import datetime

from django.core.mail import send_mail
from django.shortcuts import redirect
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme

from core.models import Notification


# --- Notifications (FR 3.3: dashboard + email) ---
def notify(user, title, message, link=""):
    """Save a dashboard notification and send the same text by email."""
    Notification.objects.create(
        user=user, title=title, message=message, link=link
    )
    if user.email:
        send_mail(title, message, None, [user.email], fail_silently=True)


# --- Date ranges used by the dashboard date pickers ---
def month_bounds(day):
    """Return the first and last day of the month that contains "day"."""
    first = day.replace(day=1)
    last = first.replace(day=calendar.monthrange(day.year, day.month)[1])
    return first, last


def parse_date_range(request):
    """
    Read ?start=YYYY-MM-DD&end=YYYY-MM-DD from the URL.
    Falls back to the current month when the values are missing or wrong.
    """
    today = timezone.localdate()
    default_start, default_end = month_bounds(today)
    try:
        start = datetime.date.fromisoformat(request.GET.get("start", ""))
        end = datetime.date.fromisoformat(request.GET.get("end", ""))
    except ValueError:
        return default_start, default_end
    if end < start:
        start, end = end, start
    return start, end


def day_start(day):
    """Timezone-aware datetime at 00:00 on "day"."""
    return timezone.make_aware(
        datetime.datetime.combine(day, datetime.time.min)
    )


def day_end(day):
    """Timezone-aware datetime at 23:59:59 on "day"."""
    return timezone.make_aware(
        datetime.datetime.combine(day, datetime.time.max)
    )


def percent_change(current, previous):
    """Percentage change between two numbers, rounded to one decimal."""
    if not previous:
        return 0.0 if not current else 100.0
    return round((current - previous) / previous * 100, 1)


# --- Month grid used by the booking and schedule calendars ---
def month_grid(year, month):
    """
    A list of weeks for one month. Each week is a list of 7 dates that
    starts on Sunday, like the Figma calendars.
    """
    cal = calendar.Calendar(firstweekday=6)
    return list(cal.monthdatescalendar(year, month))


def shift_month(year, month, step):
    """Move forward (step=1) or back (step=-1) by one month."""
    month += step
    if month == 0:
        return year - 1, 12
    if month == 13:
        return year + 1, 1
    return year, month


def read_month(request):
    """Read ?year=&month= from the URL, defaulting to this month."""
    today = timezone.localdate()
    try:
        year = int(request.GET.get("year", today.year))
        month = int(request.GET.get("month", today.month))
        datetime.date(year, month, 1)
    except ValueError:
        return today.year, today.month
    return year, month


def next_payout_date(today=None):
    """Payouts happen on the 24th of every month."""
    today = today or timezone.localdate()
    if today.day <= 24:
        return today.replace(day=24)
    year, month = shift_month(today.year, today.month, 1)
    return datetime.date(year, month, 24)


# --- Safe "go back" after a form button ---
def redirect_back(request, fallback):
    """Return to the page named in the form's "next" field, if it is safe."""
    next_url = request.POST.get("next") or request.GET.get("next")
    if next_url and url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}
    ):
        return redirect(next_url)
    return redirect(fallback)
