"""
PLACEHOLDER written by Ghavish in Phase 1 so every link already works.
Somanshu replaces the WHOLE content of this file with the real screen.
"""

from django.shortcuts import render

def user_management(request):
    context = {
    "screen_name": "User Management",
    "owner": "Somanshu",
    }
    return render(request, "layouts/coming_soon.html", context)

def user_detail(request, pk):
    context = {
    "screen_name": "User Management",
    "owner": "Somanshu",
    }
    return render(request, "layouts/coming_soon.html", context)
