"""Django models for the accounts app."""

from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Profile(models.Model):
    """Расширение пользователя для хранения дополнительной информации."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    telegram_id = models.BigIntegerField(null=True, blank=True, unique=True)
