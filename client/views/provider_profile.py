"""
Service Provider Profile (Khushi).
Public profile: bio, badge, rating, portfolio, contact and reviews (FR 2.6).
"""
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from core.models import ProfileView, ServiceCategory, ServiceProvider
def provider_profile(request, pk):
    provider = get_object_or_404(
    ServiceProvider.objects.select_related("user", "subscription"), pk=pk
    )
    viewer = request.user
    is_owner = viewer.is_authenticated and viewer == provider.user
    is_admin = viewer.is_authenticated and viewer.is_platform_admin

    # Pending or rejected providers are hidden from clients (FR 3.2).
    if not provider.is_public and not (is_owner or is_admin):
        raise Http404
    # Count the visit for "Portfolio Views" (the owner is not counted).
    if not is_owner:
        ProfileView.objects.create(provider=provider)
    # Only the projects allowed by the subscription tier are shown (FR 3.5).
    items = list(provider.portfolio_items.all())
    limit = provider.subscription.portfolio_limit
    visible_items = items[:limit] if limit else items
    paginator = Paginator(visible_items, 3)
    portfolio_page = paginator.get_page(request.GET.get("page"))

    is_favourite = False
    if viewer.is_authenticated and viewer.is_client:
        is_favourite = viewer.wishlist_items.filter(provider=provider).exists()

    context = {
        "provider": provider,
        "portfolio_page": portfolio_page,
        "portfolio_shown": len(portfolio_page.object_list),
        "portfolio_total": len(visible_items),
        "reviews": provider.reviews.filter(is_removed=False).select_related(
        "client"
        ),
        "categories": ServiceCategory.objects.filter(is_active=True),
        "provider_category_ids": set(
        provider.categories.values_list("pk", flat=True)
        ),
        "areas": [
        label for value, label in provider._meta.get_field(
        "district"
        ).choices if value in provider.areas_served
        ],
        "is_favourite": is_favourite,
        "can_book": viewer.is_authenticated and viewer.is_client,
        }
    return render(request, "client/provider_profile.html", context)