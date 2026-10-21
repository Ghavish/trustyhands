"""Favourites (Khushi): providers a client saved for later (FR 2.10)."""
from django.contrib import messages
from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from core.decorators import role_required
from core.models import ServiceProvider, WishlistItem
from core.utils import redirect_back

# Providers can save other providers too (they can also book them).
@role_required("CLIENT", "PROVIDER")
def favourites(request):
    items = request.user.wishlist_items.select_related(
    "provider", "provider__user"
    )
    return render(request, "client/favourites.html", {"items": items})

@role_required("CLIENT", "PROVIDER")
@require_POST
def toggle_favourite(request, pk):
    provider = get_object_or_404(ServiceProvider, pk=pk)
    if provider.user == request.user:
        messages.error(request, _("You cannot save your own profile."))
        return redirect_back(request, "client:favourites")
    item = WishlistItem.objects.filter(
        client=request.user, provider=provider
    ).first()
    if item:
        item.delete()
        messages.info(request, _("Removed from your favourites."))
    else:
        WishlistItem.objects.create(client=request.user, provider=provider)
        messages.success(request, _("Saved to your favourites."))
    return redirect_back(request, "client:favourites")
