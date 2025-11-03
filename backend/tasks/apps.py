"""Django app configuration for the tasks app."""

from django.apps import AppConfig


class TasksConfig(AppConfig):
    """Конфигурация приложения tasks."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "tasks"
