import uuid

from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from core.decorators import provider_profile_required
from core.models import Payment, PlanChangeLog, Subscription

PLANS = [
    {
        "tier": "STARTER",
        "features": [
            gettext_lazy("Standard Search Ranking"),
            gettext_lazy("3 Projects Portfolio Limit"),
            gettext_lazy("Standard Email Support"),
        ],
    },
    {
        "tier": "PRO",
        "popular": True,
        "features": [
            gettext_lazy("Priority Search Ranking Boost"),
            gettext_lazy("15 Projects Portfolio Limit"),
            gettext_lazy("Verified Pro Badge"),
            gettext_lazy("Direct Client Messaging"),
        ],
    },
    {
        "tier": "ELITE",
        "features": [
            gettext_lazy("Top-tier Featured Placement"),
            gettext_lazy("Unlimited Projects Showcase"),
            gettext_lazy("Master Tradesperson Badge"),
            gettext_lazy("24/7 Dedicated Phone Support"),
        ],
    },
]


def apply_plan(provider, tier, cycle, changed_by):
    """Save the new plan and log the change."""
    subscription = provider.subscription
    PlanChangeLog.objects.create(
        provider=provider, changed_by=changed_by,
        old_tier=subscription.tier, new_tier=tier,
        old_cycle=subscription.billing_cycle, new_cycle=cycle,
    )
    subscription.tier = tier
    subscription.billing_cycle = cycle
    subscription.started_at = timezone.now()
    subscription.save()


@provider_profile_required
def choose_plan(request):
    provider = request.provider
    subscription = provider.subscription

    if request.method == "POST":
        tier = request.POST.get("tier")
        cycle = request.POST.get("billing_cycle", "MONTHLY")
        if tier not in Subscription.Tier.values:
            return redirect("provider:choose_plan")
        if cycle not in Subscription.BillingCycle.values:
            cycle = "MONTHLY"
        if tier == Subscription.Tier.STARTER:
            apply_plan(provider, tier, cycle, request.user)
            items = provider.portfolio_items.count()
            if items > 3:
                messages.warning(
                    request,
                    _("Starter shows 3 projects publicly. Upgrade to show "
                      "all %(count)s.") % {"count": items},
                )
            messages.success(request, _("You are on the Starter plan."))
            return redirect("provider:active_jobs")
        # Paid plan: remember the choice, then show the checkout page.
        request.session["pending_plan"] = {"tier": tier, "cycle": cycle}
        return redirect("provider:checkout")

    plans = []
    for plan in PLANS:
        tier = plan["tier"]
        plans.append({
            **plan,
            "label": Subscription.Tier(tier).label,
            "monthly": Subscription.price_for(tier, "MONTHLY"),
            "annual": Subscription.price_for(tier, "ANNUAL"),
            "is_current": tier == subscription.tier,
        })
    context = {
        "plans": plans,
        "subscription": subscription,
        "first_time": not provider.payments.exists()
        and not provider.plan_logs.exists(),
    }
    return render(request, "service_provider/choose_plan.html", context)


@provider_profile_required
def checkout(request):
    pending = request.session.get("pending_plan")
    if not pending:
        return redirect("provider:choose_plan")
    tier, cycle = pending["tier"], pending["cycle"]
    amount = Subscription.price_for(tier, cycle)

    if request.method == "POST":
        payment = Payment.objects.create(
            provider=request.provider, tier=tier, billing_cycle=cycle,
            amount=amount, reference=f"PAY-{uuid.uuid4().hex[:8].upper()}",
        )
        apply_plan(request.provider, tier, cycle, request.user)
        del request.session["pending_plan"]
        messages.success(
            request,
            _("Payment %(ref)s confirmed. Welcome to %(plan)s!")
            % {"ref": payment.reference, "plan": Subscription.Tier(tier).label},
        )
        return redirect("provider:active_jobs")

    context = {
        "tier_label": Subscription.Tier(tier).label,
        "cycle_label": Subscription.BillingCycle(cycle).label,
        "amount": amount,
    }
    return render(request, "service_provider/checkout.html", context)
