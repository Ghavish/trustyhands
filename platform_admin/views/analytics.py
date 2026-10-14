"""
Analytics Dashboard (Somanshu). FR 7.5: pending verifications, approvals,
transactions, active clients per category, requests per week and
top-rated providers.
"""

import datetime
from decimal import Decimal

from django.db.models import Sum
from django.shortcuts import render

from core.decorators import admin_required
from core.models import (
    Payment, ServiceCategory, ServiceProvider, ServiceRequest, VerificationLog,
)
from core.utils import day_end, day_start, parse_date_range, percent_change
from users.models import User


def money_in(start, end):
    """Subscription payments plus completed job amounts in the range."""
    since, until = day_start(start), day_end(end)
    payments = Payment.objects.filter(
        created_at__range=(since, until)
    ).aggregate(total=Sum("amount"))["total"] or Decimal(0)
    jobs = ServiceRequest.objects.filter(
        status=ServiceRequest.Status.COMPLETED,
        completed_at__range=(since, until),
    ).aggregate(total=Sum("final_amount"))["total"] or Decimal(0)
    return payments + jobs


def approvals_between(start, end):
    return VerificationLog.objects.filter(
        action=VerificationLog.Action.APPROVE,
        created_at__range=(day_start(start), day_end(end)),
    ).count()


def submissions_between(start, end):
    return ServiceProvider.objects.filter(
        submitted_at__range=(day_start(start), day_end(end))
    ).count()


@admin_required
def analytics_dashboard(request):
    start, end = parse_date_range(request)
    length = (end - start).days + 1
    prev_end = start - datetime.timedelta(days=1)
    prev_start = prev_end - datetime.timedelta(days=length - 1)

    pending = ServiceProvider.objects.filter(
        verification_status__in=["PENDING", "MORE_INFO"]
    ).count()
    approvals = approvals_between(start, end)
    transactions = money_in(start, end)

    # Running total of money per day, for the orange line.
    money_trend, running = [], Decimal(0)
    for offset in range(length):
        day = start + datetime.timedelta(days=offset)
        running += money_in(day, day)
        money_trend.append(float(running))

    # Active clients who booked in each category (doughnut chart).
    active_clients = User.objects.filter(
        role=User.Role.CLIENT, account_status=User.AccountStatus.ACTIVE
    )
    category_rows = []
    for category in ServiceCategory.objects.filter(is_active=True):
        clients = set(
            ServiceRequest.objects.filter(
                category=category, client__in=active_clients
            ).values_list("client_id", flat=True)
        )
        category_rows.append({
            "name": category.name,
            "clients": len(clients),
            "providers": category.providers.filter(
                verification_status="APPROVED"
            ).count(),
        })

    # Requests per week, last 8 weeks.
    weekly = []
    week_end = end
    for _ in range(8):
        week_start = week_end - datetime.timedelta(days=6)
        weekly.insert(0, ServiceRequest.objects.filter(
            created_at__range=(day_start(week_start), day_end(week_end))
        ).count())
        week_end = week_start - datetime.timedelta(days=1)

    top_rated = ServiceProvider.objects.filter(
        verification_status="APPROVED", review_count__gt=0
    ).order_by("-average_rating", "-review_count")[:5]

    context = {
        "range_start": start,
        "range_end": end,
        "pending": pending,
        "pending_change": percent_change(
            submissions_between(start, end),
            submissions_between(prev_start, prev_end),
        ),
        "approvals": approvals,
        "approvals_change": percent_change(
            approvals, approvals_between(prev_start, prev_end)
        ),
        "transactions": transactions,
        "transactions_change": percent_change(
            float(transactions), float(money_in(prev_start, prev_end))
        ),
        "money_trend": money_trend,
        "active_clients": active_clients.count(),
        "category_rows": category_rows,
        "category_labels": [row["name"] for row in category_rows],
        "category_values": [row["clients"] for row in category_rows],
        "weekly": weekly,
        "total_users": User.objects.count(),
        "top_rated": top_rated,
    }
    return render(request, "platform_admin/analytics.html", context)
