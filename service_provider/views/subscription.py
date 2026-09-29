"""
PLACEHOLDER written by Ghavish in Phase 1 so every link already works.
Yashmeeta replaces the WHOLE content of this file with the real screen.
"""

from django.shortcuts import render

def choose_plan(request):
    context = {
    "screen_name": "Subscription",
    "owner": "Yashmeeta",
    }
    return render(request, "layouts/coming_soon.html", context)

def checkout(request):
    context = {
    "screen_name": "Subscription",
    "owner": "Yashmeeta",
    }
    return render(request, "layouts/coming_soon.html", context)
