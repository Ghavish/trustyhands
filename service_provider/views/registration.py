"""
PLACEHOLDER written by Ghavish in Phase 1 so every link already works.
Yashmeeta replaces the WHOLE content of this file with the real screen.
"""

from django.shortcuts import render

def portfolio_hub(request):
    context = {
    "screen_name": "Service Provider Registration",
    "owner": "Yashmeeta",
    }
    return render(request, "layouts/coming_soon.html", context)