"""Form pieces reused by several screens."""

from django import forms
from django.utils.translation import gettext_lazy as _


class MultipleFileInput(forms.ClearableFileInput):
    """A file picker that lets the user choose several files at once."""

    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    """Returns a list of uploaded files instead of one file."""

    def __init__(self, *args, max_files=10, **kwargs):
        self.max_files = max_files
        kwargs.setdefault("widget", MultipleFileInput(attrs={"multiple": True}))
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_clean = super().clean
        if isinstance(data, (list, tuple)):
            files = [single_clean(item, initial) for item in data if item]
        elif data:
            files = [single_clean(data, initial)]
        else:
            files = []
        if len(files) > self.max_files:
            raise forms.ValidationError(
                _("You can upload up to %(max)s files."),
                params={"max": self.max_files},
            )
        return files


class MultipleImageField(MultipleFileField):
    """Same as MultipleFileField but checks that every file is an image."""

    def clean(self, data, initial=None):
        files = super().clean(data, initial)
        image_check = forms.ImageField()
        return [image_check.clean(item) for item in files]
