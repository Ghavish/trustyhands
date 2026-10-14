
from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _

from core.decorators import admin_required
from core.models import Review


@admin_required
def review_moderation(request):
    if request.method == "POST":
        review = get_object_or_404(Review, pk=request.POST.get("review_id"))
        reason = request.POST.get("reason", "").strip()
        if not reason:
            messages.error(request, _("Please give a reason for removing it."))
        else:
            review.is_removed = True
            review.removed_reason = reason
            review.removed_by = request.user
            review.removed_at = timezone.now()
            review.save()  # also recalculates the provider's rating
            messages.success(request, _("The review was removed."))
        return redirect(request.get_full_path())

    show = request.GET.get("show", "visible")
    reviews = Review.objects.select_related(
        "client", "provider", "request", "removed_by"
    )
    if show == "visible":
        reviews = reviews.filter(is_removed=False)
    elif show == "removed":
        reviews = reviews.filter(is_removed=True)

    page = Paginator(reviews, 10).get_page(request.GET.get("page"))
    return render(
        request,
        "platform_admin/review_moderation.html",
        {"page_obj": page, "show": show},
    )
