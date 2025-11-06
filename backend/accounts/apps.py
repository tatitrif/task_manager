"""Django app configuration for the accounts app."""

from django.apps import AppConfig


class AccountsConfig(AppConfig):  # noqa
    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"
