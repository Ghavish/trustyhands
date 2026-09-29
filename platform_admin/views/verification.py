"""
PLACEHOLDER written by Ghavish in Phase 1 so every link already works.
Somanshu replaces the WHOLE content of this file with the real screen.
"""

from django.shortcuts import render

def verification_queue(request):
    context = {
    "screen_name": "Verification Queue",
    "owner": "Somanshu",
    }
    return render(request, "layouts/coming_soon.html", context)

def verification_detail(request, pk):
    context = {
    "screen_name": "Verification Queue",
    "owner": "Somanshu",
    }
    return render(request, "layouts/coming_soon.html", context)