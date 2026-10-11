"""
Earnings Overview (Meer). Payouts and bank details are simulated,
but every withdrawal and bank change is saved.
"""

import calendar
import datetime
from decimal import Decimal

from django import forms
from django.contrib import messages
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from core.choices import JobType
from core.decorators import provider_profile_required
from core.models import BankDetailsLog, Payout, ServiceRequest
from core.utils import (
    day_end, day_start, month_bounds, next_payout_date, parse_date_range,
)

COMPLETED = ServiceRequest.Status.COMPLETED


class BankForm(forms.Form):
    bank_name = forms.CharField(label=gettext_lazy("Bank"), max_length=60)
    account_number = forms.RegexField(
        label=gettext_lazy("Account number"),
        regex=r"^\d{6,20}$",
        error_messages={"invalid": gettext_lazy("Digits only (6 to 20).")},
    )


def total(queryset):
    return queryset.aggregate(total=Sum("final_amount"))["total"] or Decimal(0)


def monthly_totals(jobs, year, last_month):
    """Earnings for each month from January to "last_month"."""
    values = []
    for month in range(1, last_month + 1):
        first = datetime.date(year, month, 1)
        last = first.replace(day=calendar.monthrange(year, month)[1])
        values.append(float(total(jobs.filter(
            completed_at__range=(day_start(first), day_end(last))
        ))))
    return values


@provider_profile_required
def earnings_overview(request):
    provider = request.provider
    completed = provider.requests.filter(status=COMPLETED)
    today = timezone.localdate()
    action = request.POST.get("action")
    bank_form = BankForm()

    # --- Withdraw every job that is not paid out yet ---
    if request.method == "POST" and action == "withdraw":
        unpaid = completed.filter(payout_status="PENDING")
        amount = total(unpaid)
        if not provider.bank_account_number:
            messages.error(request, _("Please add your bank account first."))
        elif amount <= 0:
            messages.error(request, _("There is nothing to withdraw yet."))
        else:
            Payout.objects.create(
                provider=provider, amount=amount, status=Payout.Status.PAID,
                bank_label=provider.bank_label, paid_at=timezone.now(),
            )
            unpaid.update(payout_status="PAID")
            messages.success(
                request, _("MUR %(amount)s sent to %(bank)s.")
                % {"amount": f"{amount:,.0f}", "bank": provider.bank_label},
            )
        return redirect("provider:earnings_overview")

    # --- Update the bank account ---
    if request.method == "POST" and action == "update_bank":
        bank_form = BankForm(request.POST)
        if bank_form.is_valid():
            provider.bank_name = bank_form.cleaned_data["bank_name"]
            provider.bank_account_number = bank_form.cleaned_data["account_number"]
            provider.save(update_fields=["bank_name", "bank_account_number"])
            BankDetailsLog.objects.create(
                provider=provider, bank_name=provider.bank_name,
                account_ending=provider.bank_account_number[-4:],
            )
            messages.success(request, _("Bank account updated."))
            return redirect("provider:earnings_overview")

    # --- Transactions table: date range, search and job type filter ---
    start, end = parse_date_range(request)
    transactions = completed.filter(
        completed_at__range=(day_start(start), day_end(end))
    ).select_related("client").order_by("-completed_at")
    search = request.GET.get("q", "").strip()
    if search:
        transactions = transactions.filter(
            Q(reference__icontains=search)
            | Q(client__first_name__icontains=search)
            | Q(client__last_name__icontains=search)
        )
    job_type = request.GET.get("type", "")
    if job_type in JobType.values:
        transactions = transactions.filter(job_type=job_type)

    month_start, month_end = month_bounds(today)
    this_month = completed.filter(
        completed_at__range=(day_start(month_start), day_end(month_end))
    )
    # Running total of this month's earnings, one value per day so far.
    day_values, running = [], 0.0
    for n in range(today.day):
        day = month_start + datetime.timedelta(days=n)
        running += float(total(this_month.filter(
            completed_at__range=(day_start(day), day_end(day))
        )))
        day_values.append(running)

    context = {
        "range_start": start,
        "range_end": end,
        "lifetime": total(completed),
        "available": total(completed.filter(payout_status="PENDING")),
        "this_month": total(this_month),
        "month_trend": day_values,
        "next_payout": next_payout_date(today),
        "chart_labels": [
            calendar.month_abbr[m] for m in range(1, today.month + 1)
        ],
        "chart_values": monthly_totals(completed, today.year, today.month),
        "transactions": transactions,
        "search": search,
        "job_type": job_type,
        "job_types": JobType.choices,
        "payouts": provider.payouts.all()[:3],
        "bank_form": bank_form,
        "provider": provider,
    }
    return render(request, "service_provider/earnings.html", context)


@provider_profile_required
def invoice(request, pk):
    job = get_object_or_404(
        ServiceRequest.objects.select_related("client"),
        pk=pk, provider=request.provider, status=COMPLETED,
    )
    return render(
        request, "service_provider/invoice.html",
        {"job": job, "provider": request.provider},
    )
