"""
Reviews and Replies (Muneesh). FR 3.14 and 3.15.
A provider sees the reviews they received and can reply once to each.
"""

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from core.decorators import provider_profile_required
from core.models import Review


@provider_profile_required
def provider_reviews(request):
    provider = request.provider
    reviews = provider.reviews.filter(is_removed=False).select_related("client")
    breakdown = []
    total = reviews.count()
    for stars in range(5, 0, -1):
        count = reviews.filter(rating=stars).count()
        percent = round(count / total * 100) if total else 0
        breakdown.append({"stars": stars, "count": count, "percent": percent})
    context = {
        "reviews": reviews,
        "breakdown": breakdown,
        "provider": provider,
        "waiting": reviews.filter(provider_reply="").count(),
    }
    return render(request, "service_provider/reviews.html", context)


@provider_profile_required
@require_POST
def reply_review(request, pk):
    review = get_object_or_404(Review, pk=pk, provider=request.provider)
    reply = request.POST.get("reply", "").strip()
    if review.provider_reply:
        messages.error(request, _("You already replied to this review."))
    elif not reply:
        messages.error(request, _("Please write a reply."))
    else:
        review.provider_reply = reply
        review.replied_at = timezone.now()
        review.save()
        messages.success(request, _("Your reply is now public."))
    return redirect("provider:provider_reviews")
