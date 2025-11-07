"""URL patterns for the accounts app."""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

urlpatterns = [
    path("telegram/link/", views.GenerateTgLinkView.as_view(), name="tg-link"),
    path("telegram/confirm/", views.ConfirmTgLinkView.as_view(), name="tg-confirm"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
