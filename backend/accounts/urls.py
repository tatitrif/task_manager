"""URL patterns for the accounts app."""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView

from . import views

urlpatterns = [
    path("auth/telegram/link/", views.GenerateTgLinkView.as_view(), name="tg-link"),
    path(
        "auth/telegram/confirm/", views.ConfirmTgLinkView.as_view(), name="tg-confirm"
    ),
    path("auth/register/", views.RegisterView.as_view(), name="register"),
    path("auth/logout/", views.LogoutView.as_view(), name="logout"),
    path("auth/token/", TokenObtainPairView.as_view(), name="token"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
