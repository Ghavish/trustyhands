"""
Service Provider screen (Khushi).
Lists verified providers with filters and the tier-based ranking (FR 4.1).
"""
from django.db.models import Q
from django.shortcuts import render
from core.choices import Availability, ProjectScale
from core.models import ServiceCategory, ServiceProvider, Subscription

def rank_providers(providers, client_district, closest_first, rating_first):
   """
    Default order (FR 4.1): subscription tier, then rating, then completed
    jobs, then distance. The "Closest" and "Ratings" filters move their
    value to the front of the order.
    """
   def sort_key(provider):
        tier = Subscription.SEARCH_RANK[provider.tier]
        nearby = int(bool(client_district) and provider.district == client_district)
        key = [tier, provider.average_rating, provider.completed_jobs_count, nearby]
        if rating_first:
            key.insert(0, provider.average_rating)
        if closest_first:
            key.insert(0, nearby)
        return key
 
   return sorted(providers, key=sort_key, reverse=True)
 
 
def provider_list(request):
    categories = ServiceCategory.objects.filter(is_active=True)
 
    # --- Read the filters from the URL --
    category_slug = request.GET.get("category", "")
    keyword = request.GET.get("q", "").strip()
    closest = request.GET.get("closest") == "on"
    ratings = request.GET.get("ratings") == "on"
    available_only = request.GET.get("availability") == "on"
    scale = request.GET.get("scale", "")
 
    # --- Only approved providers with active accounts are public --
    providers = ServiceProvider.objects.filter(
        verification_status=ServiceProvider.VerificationStatus.APPROVED,
        user__is_active=True,
    ).select_related("user", "subscription")
 
    selected_category = categories.filter(slug=category_slug).first()
    if selected_category:
        providers = providers.filter(categories=selected_category)
    if keyword:
        providers = providers.filter(
            Q(business_name__icontains=keyword)
            | Q(profession_title__icontains=keyword)
            | Q(bio__icontains=keyword)
            | Q(town__icontains=keyword)
        )
    if available_only:
        providers = providers.filter(availability=Availability.AVAILABLE)
    if scale in ProjectScale.values:
        providers = providers.filter(project_scale=scale)
 
    client_district = ""
    favourite_ids = set()
    if request.user.is_authenticated:
        client_district = request.user.district
        favourite_ids = set(
            request.user.wishlist_items.values_list("provider_id", flat=True)
        )
 
    ranked = rank_providers(list(providers), client_district, closest, ratings)
    for provider in ranked:
        provider.top_services = list(provider.services.all()[:2])
        provider.is_favourite = provider.pk in favourite_ids
 
    context = {
        "providers": ranked,
        "categories": categories,
        "selected_category": selected_category,
        "keyword": keyword,
        "closest": closest,
        "ratings": ratings,
        "available_only": available_only,
        "scale": scale,
        "scales": ProjectScale.choices,
    }
    return render(request, "client/provider_list.html", context)
