"""About Us and Careers (Muneesh).
Both use the "coming soon" layout until their real content is written."""

from django.shortcuts import render
from django.utils.translation import gettext as _


def about(request):
    context = {"screen_name": _("About Us"), "owner": _("The TrustyHands team")}
    return render(request, "layouts/coming_soon.html", context)


def careers(request):
    context = {"screen_name": _("Careers"), "owner": _("The TrustyHands team")}
    return render(request, "layouts/coming_soon.html", context)
