"""Notifications (Yashmeeta): dashboard messages for a provider (FR 3.3)."""

from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from core.decorators import provider_profile_required


@provider_profile_required
def notifications(request):
    items = request.user.notifications.all()[:50]
    return render(
        request, "service_provider/notifications.html", {"items": items}
    )


@provider_profile_required
@require_POST
def mark_all_read(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    messages.success(request, _("All notifications marked as read."))
    return redirect("provider:notifications")
