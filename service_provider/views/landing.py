"""
Service Provider landing page (Yashmeeta).
The same long page as the client landing page, with a
"Service Provider Dashboard" button in the navbar instead of "Book Now".
"""

from django.shortcuts import render

from core.views.landing import landing_context


def provider_landing(request):
    context = landing_context(show_dashboard_button=True)
    return render(request, "core/landing.html", context)
