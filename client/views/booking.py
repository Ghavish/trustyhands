"""
PLACEHOLDER written by Ghavish in Phase 1 so every link already works.
Meer replaces the WHOLE content of this file with the real screen.
"""

from django.shortcuts import render

def book_service(request, pk):
    context = {
    "screen_name": "Service Booking",
    "owner": "Meer",
    }
    return render(request, "layouts/coming_soon.html", context)
