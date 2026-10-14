"""
Category Management (Somanshu). FR 5.1 two groups, FR 5.2 add / edit /
deactivate / remove, FR 5.3 link a verified provider to categories.
"""

from django import forms
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from core.decorators import admin_required
from core.models import ServiceCategory, ServiceProvider


class CategoryForm(forms.ModelForm):
    class Meta:
        model = ServiceCategory
        fields = ["name", "group", "description", "icon", "display_order", "is_active"]
        widgets = {"description": forms.Textarea(attrs={"rows": 2})}

    def save(self, commit=True):
        category = super().save(commit=False)
        if not category.slug:
            base = slugify(category.name) or "category"
            slug, number = base, 2
            while ServiceCategory.objects.filter(slug=slug).exists():
                slug, number = f"{base}-{number}", number + 1
            category.slug = slug
        if commit:
            category.save()
        return category


class LinkForm(forms.Form):
    provider = forms.ModelChoiceField(
        label=gettext_lazy("Verified provider"),
        queryset=ServiceProvider.objects.filter(verification_status="APPROVED"),
    )
    categories = forms.ModelMultipleChoiceField(
        label=gettext_lazy("Categories"),
        queryset=ServiceCategory.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )


@admin_required
def category_management(request):
    editing = None
    if request.GET.get("edit"):
        editing = get_object_or_404(ServiceCategory, pk=request.GET["edit"])
    form = CategoryForm(instance=editing)
    link_form = LinkForm()
    action = request.POST.get("action")

    if request.method == "POST" and action == "save":
        form = CategoryForm(request.POST, request.FILES, instance=editing)
        if form.is_valid():
            form.save()
            messages.success(request, _("Category saved."))
            return redirect("dashboard:category_management")

    elif request.method == "POST" and action == "toggle":
        category = get_object_or_404(ServiceCategory, pk=request.POST["category_id"])
        category.is_active = not category.is_active
        category.save(update_fields=["is_active"])
        messages.success(request, _("Category updated."))
        return redirect("dashboard:category_management")

    elif request.method == "POST" and action == "delete":
        category = get_object_or_404(ServiceCategory, pk=request.POST["category_id"])
        category.delete()
        messages.info(request, _("Category removed."))
        return redirect("dashboard:category_management")

    elif request.method == "POST" and action == "link":
        link_form = LinkForm(request.POST)
        if link_form.is_valid():
            provider = link_form.cleaned_data["provider"]
            provider.categories.set(link_form.cleaned_data["categories"])
            messages.success(
                request, _("Categories of %(name)s saved.")
                % {"name": provider.business_name},
            )
            return redirect("dashboard:category_management")

    categories = ServiceCategory.objects.all()
    for category in categories:
        category.provider_count = category.providers.count()
    context = {
        "categories": categories,
        "form": form,
        "editing": editing,
        "link_form": link_form,
    }
    return render(request, "platform_admin/categories.html", context)
