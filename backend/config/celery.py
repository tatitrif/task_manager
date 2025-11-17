"""Celery config."""

import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
app = Celery("config")

# автоматически находит tasks.py во всех приложениях Django
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# Добавляем периодическую задачу
app.conf.beat_schedule = {
    "check-overdue-tasks": {
        "task": "notify.cron_tasks.check_overdue_tasks",  # Путь к таску
        "schedule": crontab(minute="*/5"),  # Проверять каждые 5 минут
    },
}
