"""
User Management (Somanshu). FR 7.3 list and open accounts, FR 7.4
suspend / deactivate / restore, FR 7.6 override a provider's plan.
"""

from django import forms
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from core.models import AccountStatusLog, PlanChangeLog, Subscription
from core.decorators import admin_required
from core.utils import notify
from users.models import User


class StatusForm(forms.Form):
    account_status = forms.ChoiceField(
        label=gettext_lazy("Account Status"), choices=User.AccountStatus.choices
    )
    reason = forms.CharField(
        label=gettext_lazy("Reason"), max_length=255, required=False
    )


class PlanOverrideForm(forms.ModelForm):
    class Meta:
        model = Subscription
        fields = ["tier", "billing_cycle", "commission_rate"]
        labels = {"commission_rate": gettext_lazy("Commission rate (%)")}


@admin_required
def user_management(request):
    users = User.objects.order_by("-date_joined")
    search = request.GET.get("q", "").strip()
    role = request.GET.get("role", "")
    status = request.GET.get("status", "")
    if search:
        users = users.filter(
            Q(first_name__icontains=search)
            | Q(last_name__icontains=search)
            | Q(email__icontains=search)
        )
    if role in User.Role.values:
        users = users.filter(role=role)
    if status in User.AccountStatus.values:
        users = users.filter(account_status=status)

    context = {
        "page_obj": Paginator(users, 7).get_page(request.GET.get("page")),
        "search": search,
        "role": role,
        "status": status,
        "roles": User.Role.choices,
        "statuses": User.AccountStatus.choices,
    }
    return render(request, "platform_admin/user_management.html", context)


@admin_required
def user_detail(request, pk):
    person = get_object_or_404(User, pk=pk)
    provider = getattr(person, "provider_profile", None)
    subscription = getattr(provider, "subscription", None) if provider else None
    status_form = StatusForm(initial={"account_status": person.account_status})
    plan_form = PlanOverrideForm(instance=subscription) if subscription else None
    action = request.POST.get("action")

    if request.method == "POST" and action == "status":
        status_form = StatusForm(request.POST)
        if person == request.user:
            messages.error(request, _("You cannot change your own account."))
        elif status_form.is_valid():
            new_status = status_form.cleaned_data["account_status"]
            reason = status_form.cleaned_data["reason"]
            AccountStatusLog.objects.create(
                user=person, admin=request.user,
                old_status=person.account_status, new_status=new_status,
                reason=reason,
            )
            person.account_status = new_status
            person.status_reason = reason
            person.save()
            notify(
                person, _("Your account status changed"),
                _("New status: %(status)s. %(reason)s")
                % {"status": person.get_account_status_display(),
                   "reason": reason},
            )
            messages.success(request, _("Account status saved."))
            return redirect("dashboard:user_detail", pk=person.pk)

    if request.method == "POST" and action == "plan" and subscription:
        old = (subscription.tier, subscription.billing_cycle,
               subscription.commission_rate)
        plan_form = PlanOverrideForm(request.POST, instance=subscription)
        if plan_form.is_valid():
            plan_form.save()
            PlanChangeLog.objects.create(
                provider=provider, changed_by=request.user,
                old_tier=old[0], new_tier=subscription.tier,
                old_cycle=old[1], new_cycle=subscription.billing_cycle,
                old_commission=old[2],
                new_commission=subscription.commission_rate,
            )
            messages.success(request, _("Subscription updated."))
            return redirect("dashboard:user_detail", pk=person.pk)

    context = {
        "person": person,
        "provider": provider,
        "subscription": subscription,
        "status_form": status_form,
        "plan_form": plan_form,
        "requests": person.service_requests.select_related("provider")[:10],
        "status_logs": person.status_logs.select_related("admin"),
        "plan_logs": provider.plan_logs.all()[:5] if provider else [],
    }
    return render(request, "platform_admin/user_detail.html", context)
