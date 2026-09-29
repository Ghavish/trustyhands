"""
PLACEHOLDER written by Ghavish in Phase 1 so every link already works.
Meer replaces the WHOLE content of this file with the real screen.
"""

from django.shortcuts import redirect, render

def schedule_manager(request):
    context = {
    "screen_name": "Schedule Manager",
    "owner": "Meer",
    }
    return render(request, "layouts/coming_soon.html", context)

def delete_blocked_date(request, pk):
    return redirect("core:home")

def delete_blocked_time(request, pk):
    return redirect("core:home")
