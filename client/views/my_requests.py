"""
PLACEHOLDER written by Ghavish in Phase 1 so every link already works.
Khushi replaces the WHOLE content of this file with the real screen.
"""

from django.shortcuts import redirect, render

def my_requests(request):
    context = {
    "screen_name": "My Requests",
    "owner": "Khushi",
    }
    return render(request, "layouts/coming_soon.html", context)

def cancel_request(request, pk):
    return redirect("core:home")

def leave_review(request, pk):
    return redirect("core:home")