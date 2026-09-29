from django.urls import path

from core.views.landing import after_login, client_landing
from core.views.preferences import set_preferences

app_name = "core"

urlpatterns = [
    path("", client_landing, name="home"),
    path("welcome/", after_login, name="after_login"),
    path("preferences/", set_preferences, name="set_preferences"),
]
