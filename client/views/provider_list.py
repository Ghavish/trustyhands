"""
Service Provider screen (Khushi).
Lists verified providers with filters and the tier-based ranking (FR 4.1).
"""
from django.db.models import Q
from django.shortcuts import render
from core.choices import Availability, District, ProjectScale
from core.models import ServiceCategory, ServiceProvider, Subscription

# Order of the stops on the "Project Scale" slider ("" means Any).
SCALE_STOPS = [("", "Any")] + list(ProjectScale.choices)

def serves_district(provider, district):
    """True when the provider is based in, or travels to, the district."""
    if not district:
        return False
    return (
        provider.district == district
        or district in provider.areas_served
        or District.ISLAND_WIDE in provider.areas_served
    )

def rank_providers(providers, client_district, closest_first, rating_first):
    """
    Default order (FR 4.1): subscription tier, then rating, then completed
    jobs, then distance. The "Closest" and "Ratings" filters move their
    value to the front of the order.
    """
    def sort_key(provider):
        tier = Subscription.SEARCH_RANK[provider.tier]
        nearby = int(serves_district(provider, client_district))
        key = [tier, provider.average_rating, provider.completed_jobs_count, nearby]
        if rating_first:
            key.insert(0, provider.average_rating)
        if closest_first:
            key.insert(0, nearby)
        return key

    return sorted(providers, key=sort_key, reverse=True)

def card_services(provider):
    """
    Up to two services for the card, each with an icon.
    A service without its own icon borrows its category's icon. A provider
    who has not added services yet shows their categories instead, so the
    "Services" column is never blank.
    """
    services = []
    for service in provider.services.select_related("category")[:2]:
        icon = service.icon or (service.category.icon if service.category else None)
        services.append({"name": service.name, "icon": icon or None})
    if not services:
        for category in provider.categories.all()[:2]:
            services.append({"name": category.name, "icon": category.icon or None})
    return services

def provider_list(request):
    categories = ServiceCategory.objects.filter(is_active=True)

    # --- Read the filters from the URL ---
    category_slug = request.GET.get("category", "")
    keyword = request.GET.get("q", "").strip()
    closest = request.GET.get("closest") == "on"
    ratings = request.GET.get("ratings") == "on"
    available_only = request.GET.get("availability") == "on"
    scale = request.GET.get("scale", "")
    if scale not in ProjectScale.values:
        scale = ""
    # "Closest" asks the visitor for their district each time.
    # The choice only lives in the URL; it is not saved to the profile.
    district = request.GET.get("district", "")
    if district not in District.values or district == District.ISLAND_WIDE:
        district = ""

    # --- Only approved providers with active accounts are public ---
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
    if scale:
        providers = providers.filter(project_scale=scale)

    favourite_ids = set()
    if request.user.is_authenticated:
        favourite_ids = set(
            request.user.wishlist_items.values_list("provider_id", flat=True)
        )

    ranked = rank_providers(
        list(providers), district if closest else "", closest, ratings
    )
    for provider in ranked:
        provider.top_services = card_services(provider)
        provider.is_favourite = provider.pk in favourite_ids
        provider.is_nearby = closest and serves_district(provider, district)

    scale_values = [value for value, label in SCALE_STOPS]
    context = {
        "providers": ranked,
        "categories": categories,
        "selected_category": selected_category,
        "keyword": keyword,
        "closest": closest,
        "district": district,
        "districts": [
            (value, label) for value, label in District.choices
            if value != District.ISLAND_WIDE
        ],
        "ratings": ratings,
        "available_only": available_only,
        "scale": scale,
        "scale_stops": [
            (value, label) for value, label in [("", None)] + list(ProjectScale.choices)
        ],
        "scale_index": scale_values.index(scale),
        "scale_max": len(scale_values) - 1,
    }
    return render(request, "client/provider_list.html", context)