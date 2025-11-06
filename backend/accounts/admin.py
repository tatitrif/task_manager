"""Django admin configuration for the accounts app."""

from django.contrib import admin

from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """Админка для модели профиля пользователя."""

    list_display = ("user", "telegram_id")
    autocomplete_fields = ("user",)
