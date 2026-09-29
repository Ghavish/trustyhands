"""
PLACEHOLDER written by Ghavish in Phase 1 so every link already works.
Khushi replaces the WHOLE content of this file with the real screen.
"""

from django.shortcuts import render

def provider_list(request):
    context = {
    "screen_name": "Service Provider List",
    "owner": "Khushi",
    }
    return render(request, "layouts/coming_soon.html", context)