"""
PLACEHOLDER written by Ghavish in Phase 1 so every link already works.
Yashmeeta replaces the WHOLE content of this file with the real screen.
"""

from django.shortcuts import redirect, render

def notifications(request):
    context = {
    "screen_name": "Notifications",
    "owner": "Yashmeeta",
    }
    return render(request, "layouts/coming_soon.html", context)

def mark_all_read(request):
    return redirect("core:home")