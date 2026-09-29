"""
PLACEHOLDER written by Ghavish in Phase 1 so every link already works.
Yashmeeta replaces the WHOLE content of this file with the real screen.
"""

from django.shortcuts import render

def provider_landing(request):
    context = {
    "screen_name": "Service Provider Landing Page",
    "owner": "Yashmeeta",
    }
    return render(request, "layouts/coming_soon.html", context)
