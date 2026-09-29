"""
PLACEHOLDER written by Ghavish in Phase 1 so every link already works.
Somanshu replaces the WHOLE content of this file with the real screen.
"""

from django.shortcuts import render

def analytics_dashboard(request):
    context = {
    "screen_name": "Analytics Dashboard",
    "owner": "Somanshu",
    }
    return render(request, "layouts/coming_soon.html", context)
