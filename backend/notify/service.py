"""Notification service module for the tasks application."""

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model

from tasks.serializers import TaskSerializer
from .presence import is_online
from .telegram import send_telegram_message

User = get_user_model()
channel_layer = get_channel_layer()


def ws_send_user(user_id: int, payload: dict):
    """Send WebSocket message to a user."""
    async_to_sync(channel_layer.group_send)(
        f"user_{user_id}",
        {"type": "ws.event", "data": payload},
    )


def notify_task_change(task, action, old_assigned_to_id=None):
    """
    Отправляет уведомления заинтересованным пользователям.

    - task_updated актуализации контента
    - task_notify для assigned/unassigned сообщений
    action: "created", "updated", "deleted", "assigned"
    """
    recipients = set()

    # Новый назначенный пользователь
    if task.assigned_to_id:
        recipients.add(task.assigned_to_id)

    # Старый назначенный пользователь
    if old_assigned_to_id:
        recipients.add(old_assigned_to_id)

    # Владелец списка
    if hasattr(task, "list_tasks") and task.list_tasks and task.list_tasks.owner_id:
        recipients.add(task.list_tasks.owner_id)

    # payload для task_updated
    payload_updated = {
        "type": "task_updated",
        "action": action,
        "task": TaskSerializer(task).data,
    }

    # payload для task_notify
    payload_notify_new = {
        "type": "task_notify",
        "action": action,
        "message": f"Вам назначена задача: {task.name}",
        "task": TaskSerializer(task).data,
    }
    payload_notify_removed = {
        "type": "task_notify",
        "action": action,
        "message": f"Задача '{task.name}' больше не назначена вам",
        "task": TaskSerializer(task).data,
    }

    for user_id in recipients:
        user = User.objects.filter(id=user_id).first()
        if not user:
            continue

        # task_updated всегда
        if is_online(user.id):
            ws_send_user(user.id, payload_updated)

        if old_assigned_to_id != task.assigned_to_id:
            # task_notify только для нового и старого assigned_to
            if user.id == task.assigned_to_id:
                payload = payload_notify_new
            elif user.id == old_assigned_to_id:
                payload = payload_notify_removed
            else:
                continue  # владелец списка уведомление не получает

            if is_online(user.id):
                ws_send_user(user.id, payload)
            elif getattr(getattr(user, "profile", None), "telegram_id", None):
                send_telegram_message(user.profile.telegram_id, payload["message"])
