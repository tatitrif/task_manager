"""URL patterns for the accounts app."""

from django.urls import path

from . import views

urlpatterns = [
    path("telegram/link/", views.GenerateTgLinkView.as_view(), name="tg-link"),
    path("telegram/confirm/", views.ConfirmTgLinkView.as_view(), name="tg-confirm"),
]
