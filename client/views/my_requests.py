"""
My Requests (Khushi): a client's request history (FR 2.11), cancelling
open requests and reviewing completed ones (FR 2.9, 6.1).
"""
from django import forms
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.views.decorators.http import require_POST
from core.decorators import role_required

# Providers who booked another provider follow their requests here too.
customer_required = role_required("CLIENT", "PROVIDER")
from core.models import RequestLog, Review, ServiceRequest
from core.utils import notify
 
 
class ReviewForm(forms.ModelForm):
    rating = forms.TypedChoiceField(
        label=gettext_lazy("Rating"),
        # "\u2605" is the star character.
        choices=[(n, "\u2605" * n) for n in range(5, 0, -1)],
        coerce=int,
    )
 
    class Meta:
        model = Review
        fields = ["rating", "comment"]
        labels = {"comment": gettext_lazy("Your review")}
        widgets = {"comment": forms.Textarea(attrs={"rows": 3})}
 
 
@customer_required
def my_requests(request):
    status = request.GET.get("status", "")
    requests = request.user.service_requests.select_related(
        "provider", "category"
    )
    if status in ServiceRequest.Status.values:
        requests = requests.filter(status=status)
    reviewed_ids = set(
        Review.objects.filter(client=request.user).values_list(
            "request_id", flat=True
        )
    )
    context = {
        "requests": requests,
        "status": status,
        "statuses": ServiceRequest.Status.choices,
        "reviewed_ids": reviewed_ids,
        "review_form": ReviewForm(),
    }
    return render(request, "client/my_requests.html", context)
 
 
@customer_required
@require_POST
def cancel_request(request, pk):
    job = get_object_or_404(ServiceRequest, pk=pk, client=request.user)
    if job.status not in [
        ServiceRequest.Status.PENDING, ServiceRequest.Status.ACCEPTED
    ]:
        messages.error(request, _("This request can no longer be cancelled."))
        return redirect("client:my_requests")
    RequestLog.objects.create(
        request=job, actor=request.user, action=RequestLog.Action.STATUS,
        old_value=job.status, new_value=ServiceRequest.Status.CANCELLED,
    )
    job.status = ServiceRequest.Status.CANCELLED
    job.save(update_fields=["status", "updated_at"])
    notify(
        job.provider.user, _("Request cancelled"),
        _("%(client)s cancelled request %(ref)s.")
        % {"client": request.user.display_name, "ref": job.reference},
        reverse("provider:active_jobs"),
    )
    messages.success(request, _("Your request was cancelled."))
    return redirect("client:my_requests")
 
 
@customer_required
@require_POST
def leave_review(request, pk):
    job = get_object_or_404(ServiceRequest, pk=pk, client=request.user)
    # FR 6.1: only completed requests can be reviewed, and only once.
    if job.status != ServiceRequest.Status.COMPLETED:
        messages.error(request, _("You can review a job once it is completed."))
        return redirect("client:my_requests")
    if Review.objects.filter(request=job).exists():
        messages.error(request, _("You already reviewed this job."))
        return redirect("client:my_requests")
    form = ReviewForm(request.POST)
    if form.is_valid():
        review = form.save(commit=False)
        review.request = job
        review.client = request.user
        review.provider = job.provider
        review.save()
        notify(
            job.provider.user, _("New review"),
            _("%(client)s rated you %(stars)s/5.")
            % {"client": request.user.display_name, "stars": review.rating},
            reverse("provider:provider_reviews"),
        )
        messages.success(request, _("Thank you for your review!"))
    else:
        messages.error(request, _("Please choose a rating."))
    return redirect("client:my_requests")