"""
PLACEHOLDER written by Ghavish in Phase 1 so every link already works.
Khushi replaces the WHOLE content of this file with the real screen.
"""

from django.shortcuts import render

def edit_profile(request):
    context = {
    "screen_name": "Edit Profile",
    "owner": "Khushi",
    }
    return render(request, "layouts/coming_soon.html", context)
