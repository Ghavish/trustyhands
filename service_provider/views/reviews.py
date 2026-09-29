"""
PLACEHOLDER written by Ghavish in Phase 1 so every link already works.
Muneesh replaces the WHOLE content of this file with the real screen.
"""

from django.shortcuts import redirect, render

def provider_reviews(request):
    context = {
    "screen_name": "Reviews and Replies",
    "owner": "Muneesh",
    }
    return render(request, "layouts/coming_soon.html", context)

def reply_review(request, pk):
    return redirect("core:home")
