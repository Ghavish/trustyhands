"""
PLACEHOLDER written by Ghavish in Phase 1 so every link already works.
Muneesh replaces the WHOLE content of this file with the real screen.
"""

from django.shortcuts import redirect, render

def active_jobs(request):
    context = {
    "screen_name": "Active Jobs",
    "owner": "Muneesh",
    }
    return render(request, "layouts/coming_soon.html", context)

def job_detail(request, pk):
    context = {
    "screen_name": "Active Jobs",
    "owner": "Muneesh",
    }
    return render(request, "layouts/coming_soon.html", context)

def update_job(request, pk):
    return redirect("core:home")
