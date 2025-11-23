"""
Celery tasks for the notification system.

This module defines periodic tasks for checking overdue tasks and sending notifications
to users via WebSocket or Telegram.
"""

from celery import shared_task
from django.utils import timezone

from tasks.models import Task, TaskStatus
from tasks.serializers import TaskSerializer
from .presence import is_online
from .service import ws_send_user
from .telegram import send_telegram_message


@shared_task
def check_overdue_tasks():
    """Помечает задачи как просроченные и отправляет уведомления."""
    now = timezone.now()
    overdue_tasks = Task.objects.filter(complete_before__lt=now).exclude(
        status__in=[TaskStatus.COMPLETED, TaskStatus.OVERDUE]
    )

    for task in overdue_tasks:
        task.mark_overdue()

        payload_updated = {
            "type": "task_updated",
            "action": "updated",
            "task": TaskSerializer(task).data,
        }

        payload_notify = {
            "type": "task_notify",
            "action": "overdue",
            "message": f"Задача '{task.name}' просрочена!",
            "task": TaskSerializer(task).data,
        }

        if task.assigned_to:
            if is_online(task.assigned_to.id):
                ws_send_user(task.assigned_to.id, payload_updated)
                ws_send_user(task.assigned_to.id, payload_notify)
            elif getattr(
                getattr(task.assigned_to, "profile", None), "telegram_id", None
            ):
                send_telegram_message(
                    task.assigned_to.profile.telegram_id, payload_notify["message"]
                )
