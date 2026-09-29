"""
Main URL map. Each app has its own urls.py, all owned by Ghavish.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("accounts/", include("users.urls")),
    path("", include("client.urls")),
    path("provider/", include("service_provider.urls")),
    path("dashboard-admin/", include("platform_admin.urls")),
]

# Serve uploaded pictures and documents while developing.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
