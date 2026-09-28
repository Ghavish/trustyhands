"""
Template helpers. Load them in a template with:  {% load th_tags %}
"""

from decimal import Decimal, InvalidOperation

from django import template
from django.utils.html import format_html
from django.utils.safestring import mark_safe

register = template.Library()


# --- Icons: {% icon "calendar" %} draws a small line icon ---
ICON_PATHS = {
    "grid": '<rect x="3" y="3" width="7" height="7" rx="2"/>'
            '<rect x="14" y="3" width="7" height="7" rx="2"/>'
            '<rect x="3" y="14" width="7" height="7" rx="2"/>'
            '<rect x="14" y="14" width="7" height="7" rx="2"/>',
    "calendar": '<rect x="3" y="5" width="18" height="16" rx="2"/>'
                '<path d="M3 10h18M8 3v4M16 3v4"/>',
    "folder": '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0'
              ' 1-2 2H5a2 2 0 0 1-2-2z"/>',
    "dollar": '<circle cx="12" cy="12" r="9"/><path d="M15 9.5c0-1.4-1.3-2.5'
              '-3-2.5s-3 1-3 2.3c0 3.2 6 1.7 6 5 0 1.3-1.3 2.2-3 2.2s-3-1.1-3'
              '-2.5M12 5.5v13"/>',
    "logout": '<path d="M15 4h3a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-3M10 17l-5-5'
              ' 5-5M5 12h11"/>',
    "swap": '<path d="M4 8h14l-4-4M20 16H6l4 4"/>',
    "check-circle": '<circle cx="12" cy="12" r="9"/><path d="m8 12 3 3 5-6"/>',
    "users": '<circle cx="9" cy="8" r="4"/><path d="M2 21a7 7 0 0 1 14 0"/>'
             '<circle cx="18" cy="17" r="3"/><path d="M18 12.5v1.5M18'
             ' 20v1.5M13.5 17H15M21 17h1.5"/>',
    "user": '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
    "home": '<path d="M3 11 12 3l9 8v9a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0'
            ' 1-1-1z"/>',
    "bell": '<path d="M6 16V11a6 6 0 1 1 12 0v5l2 2H4z"/>'
            '<path d="M10 20a2 2 0 0 0 4 0"/>',
    "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9'
           'l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7'
           ' 6.3l1.4-1.4"/>',
    "moon": '<path d="M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5z"/>',
    "star": '<path d="m12 3 2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1'
            '-4.4-4.3 6.1-.9z"/>',
    "pin": '<path d="M12 21s-7-6.2-7-11a7 7 0 1 1 14 0c0 4.8-7 11-7 11z"/>'
           '<circle cx="12" cy="10" r="2.5"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "heart": '<path d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0'
             ' 5.6-7 10-7 10z"/>',
    "tag": '<path d="M3 12V4a1 1 0 0 1 1-1h8l9 9-9 9z"/>'
           '<circle cx="7.5" cy="7.5" r="1.5"/>',
    "message": '<path d="M4 5h16v11H8l-4 4z"/>',
    "chevron-down": '<path d="m6 9 6 6 6-6"/>',
    "chevron-left": '<path d="m15 6-6 6 6 6"/>',
    "chevron-right": '<path d="m9 6 6 6-6 6"/>',
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "edit": '<path d="M4 20h4L19 9l-4-4L4 16z"/>',
    "trash": '<path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13"/>',
    "phone": '<path d="M5 3h4l2 5-2.5 1.5a11 11 0 0 0 6 6L16 13l5 2v4a2 2 0'
             ' 0 1-2 2A16 16 0 0 1 3 5a2 2 0 0 1 2-2z"/>',
    "mail": '<rect x="3" y="5" width="18" height="14" rx="2"/>'
            '<path d="m3 7 9 6 9-6"/>',
    "file": '<path d="M14 3H6a1 1 0 0 0-1 1v16a1 1 0 0 0 1 1h12a1 1 0 0 0'
            ' 1-1V8z"/><path d="M14 3v5h5M9 13h6M9 17h6"/>',
    "external": '<path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0'
                ' 0 1-1-1V7a1 1 0 0 1 1-1h5"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
    "trend-up": '<path d="m3 17 6-6 4 4 8-8M15 7h6v6"/>',
    "trend-down": '<path d="m3 7 6 6 4-4 8 8M15 17h6v-6"/>',
    "shield": '<path d="M12 3 4 6v6c0 5 3.5 8 8 9 4.5-1 8-4 8-9V6z"/>'
              '<path d="m9 12 2 2 4-4"/>',
    "list": '<path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/>',
    "briefcase": '<rect x="3" y="7" width="18" height="13" rx="2"/>'
                 '<path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M3 13h18"/>',
    "alert": '<path d="M12 3 2 20h20z"/><path d="M12 10v4M12 17h.01"/>',
    "upload": '<path d="M12 16V4M7 9l5-5 5 5M4 20h16"/>',
    "camera": '<rect x="3" y="7" width="18" height="13" rx="2"/>'
              '<circle cx="12" cy="13.5" r="3.5"/><path d="M8 7l2-3h4l2 3"/>',
    "dots": '<circle cx="12" cy="5" r="1"/><circle cx="12" cy="12" r="1"/>'
            '<circle cx="12" cy="19" r="1"/>',
    "lock": '<rect x="5" y="11" width="14" height="10" rx="2"/>'
            '<path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
    "globe": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0'
             ' 0 1 0 18M12 3a14 14 0 0 0 0 18"/>',
    "menu": '<path d="M4 6h16M4 12h16M4 18h16"/>',
}


@register.simple_tag
def icon(name, size=20, css_class=""):
    paths = ICON_PATHS.get(name, "")
    return format_html(
        '<svg class="icon {}" width="{}" height="{}" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="1.8" '
        'stroke-linecap="round" stroke-linejoin="round" '
        'aria-hidden="true">{}</svg>',
        css_class, size, size, mark_safe(paths),
    )


# --- Money: {{ amount|mur }} gives "MUR 1,850" ---
@register.filter
def mur(value):
    try:
        number = Decimal(value or 0)
    except (InvalidOperation, TypeError):
        return value
    return f"MUR {number:,.0f}"


# --- Stars: {% for kind in rating|stars %} gives full/half/empty ---
@register.filter
def stars(rating):
    rating = float(rating or 0)
    result = []
    for position in range(1, 6):
        if rating >= position:
            result.append("full")
        elif rating >= position - 0.5:
            result.append("half")
        else:
            result.append("empty")
    return result


# --- Colour of a status badge: {{ job.status|status_class }} ---
STATUS_CLASSES = {
    "PENDING": "warning",
    "ACCEPTED": "info",
    "IN_PROGRESS": "success",
    "COMPLETED": "success",
    "DECLINED": "danger",
    "CANCELLED": "muted",
    "PAID": "success",
    "REQUESTED": "warning",
    "ACTIVE": "success",
    "SUSPENDED": "warning",
    "DEACTIVATED": "danger",
    "APPROVED": "success",
    "REJECTED": "danger",
    "MORE_INFO": "warning",
    "HIGH": "danger",
    "NORMAL": "warning",
}


@register.filter
def status_class(status):
    return STATUS_CLASSES.get(str(status), "muted")


# --- Initials for avatars without a photo: {{ user|initials }} ---
@register.filter
def initials(user):
    first = (getattr(user, "first_name", "") or "")[:1]
    last = (getattr(user, "last_name", "") or "")[:1]
    return (first + last).upper() or "TH"
