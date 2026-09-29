"""
PLACEHOLDER written by Ghavish in Phase 1 so every link already works.
Khushi replaces the WHOLE content of this file with the real screen.
"""

from django.shortcuts import redirect, render

def favourites(request):
    context = {
    "screen_name": "Favourites",
    "owner": "Khushi",
    }
    return render(request, "layouts/coming_soon.html", context)

def toggle_favourite(request, pk):
    return redirect("core:home")
