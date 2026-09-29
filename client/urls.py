"""Client screens. <object_id:pk> matches a MongoDB id."""

from django.urls import path

from client.views.booking import book_service
from client.views.favourites import favourites, toggle_favourite
from client.views.my_requests import cancel_request, leave_review, my_requests
from client.views.provider_list import provider_list
from client.views.provider_profile import provider_profile

app_name = "client"

urlpatterns = [
    path("services/", provider_list, name="provider_list"),
    path(
        "providers/<object_id:pk>/", provider_profile, name="provider_profile"
    ),
    path("providers/<object_id:pk>/book/", book_service, name="book_service"),
    path(
        "providers/<object_id:pk>/favourite/",
        toggle_favourite,
        name="toggle_favourite",
    ),
    path("my-requests/", my_requests, name="my_requests"),
    path(
        "my-requests/<object_id:pk>/cancel/",
        cancel_request,
        name="cancel_request",
    ),
    path(
        "my-requests/<object_id:pk>/review/", leave_review, name="leave_review"
    ),
    path("favourites/", favourites, name="favourites"),
]
