"""
Service Booking (Meer): a client sends a request to one provider (FR 2.8)
and picks a date on the provider's calendar (FR 2.12).
"""

import datetime

from django import forms
from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from core.choices import Availability
from core.decorators import client_required
from core.forms import MultipleImageField
from core.models import (
    RequestLog, ServiceProvider, ServiceRequest, ServiceRequestPhoto,
)
from core.utils import notify


def blocked_days(provider):
    """Every date the provider blocked out, as "YYYY-MM-DD" strings."""
    days = []
    for period in provider.blocked_dates.filter(
        end_date__gte=timezone.localdate()
    ):
        current = period.start_date
        while current <= period.end_date:
            days.append(current.isoformat())
            current += datetime.timedelta(days=1)
    return days


class BookingForm(forms.ModelForm):
    photos = MultipleImageField(
        label=gettext_lazy("Project Photos (Up to 10 photos)"),
        required=False, max_files=10,
    )

    class Meta:
        model = ServiceRequest
        fields = [
            "contact_name", "contact_phone", "contact_email", "location",
            "description", "category", "job_type", "urgency",
            "preferred_date",
        ]
        labels = {
            "contact_name": gettext_lazy("Name"),
            "contact_phone": gettext_lazy("Phone Number"),
            "contact_email": gettext_lazy("Email Address"),
            "location": gettext_lazy("Project Location"),
            "description": gettext_lazy("Project Description"),
            "category": gettext_lazy("Service needed"),
            "job_type": gettext_lazy("Job type"),
            "urgency": gettext_lazy("Urgency"),
        }
        widgets = {"preferred_date": forms.HiddenInput()}

    def __init__(self, *args, provider, **kwargs):
        super().__init__(*args, **kwargs)
        self.provider = provider
        self.fields["category"].queryset = provider.categories.all()
        self.fields["category"].required = True
        self.fields["preferred_date"].error_messages["required"] = _(
            "Please select a date on the calendar."
        )

    def clean_preferred_date(self):
        day = self.cleaned_data["preferred_date"]
        if day < timezone.localdate():
            raise forms.ValidationError(_("Please pick a date in the future."))
        if day.isoformat() in blocked_days(self.provider):
            raise forms.ValidationError(
                _("The professional is not available on that date.")
            )
        return day


@client_required
def book_service(request, pk):
    provider = get_object_or_404(ServiceProvider, pk=pk)
    if not provider.is_public:
        raise Http404
    if provider.availability == Availability.ON_LEAVE:
        messages.warning(request, _("This professional is on leave right now."))
        return redirect("client:provider_profile", pk=provider.pk)

    user = request.user
    initial = {
        "contact_name": user.display_name,
        "contact_phone": user.phone,
        "contact_email": user.email,
        "location": user.address,
    }
    form = BookingForm(
        request.POST or None, request.FILES or None,
        provider=provider, initial=initial,
    )
    if request.method == "POST" and form.is_valid():
        job = form.save(commit=False)
        job.client = user
        job.provider = provider
        job.save()
        for photo in form.cleaned_data["photos"]:
            ServiceRequestPhoto.objects.create(request=job, image=photo)
        RequestLog.objects.create(
            request=job, actor=user, action=RequestLog.Action.CREATED,
            new_value=job.status,
        )
        notify(
            provider.user, _("New job request"),
            _("%(client)s sent you a request: %(text)s")
            % {"client": user.display_name, "text": job.description[:60]},
            reverse("provider:active_jobs"),
        )
        messages.success(
            request, _("Your request %(ref)s was sent.") % {"ref": job.reference}
        )
        return redirect("client:my_requests")

    context = {
        "provider": provider,
        "form": form,
        "blocked": blocked_days(provider),
        "today": timezone.localdate().isoformat(),
        "photo_slots": range(10),
    }
    return render(request, "client/booking.html", context)
