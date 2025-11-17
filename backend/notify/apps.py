"""Django app configuration for the notify app."""

from django.apps import AppConfig


class NotifyConfig(AppConfig):
    """Конфигурация приложения notify."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "notify"

    def ready(self):
        """Подключаем сигналы и крон при инициализации приложения."""
        try:
            from . import signals  # noqa
            from . import cron_tasks  # noqa
        except ImportError:
            pass  # Нет файла с задачами — пропускаем
