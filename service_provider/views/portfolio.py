"""
PLACEHOLDER written by Ghavish in Phase 1 so every link already works.
Muneesh replaces the WHOLE content of this file with the real screen.
"""

from django.shortcuts import redirect, render

def portfolio_editor(request):
    context = {
    "screen_name": "Portfolio Editor",
    "owner": "Muneesh",
    }
    return render(request, "layouts/coming_soon.html", context)

def delete_project(request, pk):
    return redirect("core:home")
