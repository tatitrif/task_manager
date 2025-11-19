"""
Signal handlers for notification system.

These signals are connected to Task model to send notifications when a task is created,
updated, or deleted.
"""

from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver

from tasks.models import Task
from .service import notify_task_change

# Словарь для хранения предыдущего состояния assigned_to
_task_previous_state = {}


@receiver(pre_save, sender=Task)
def on_task_pre_save(sender, instance, **kwargs):
    """Сигнал перед сохранением задачи."""
    if instance.pk:
        try:
            # Сохраняет предыдущее состояние assigned_to.
            old_instance = Task.objects.get(pk=instance.pk)
            _task_previous_state[instance.pk] = {
                "assigned_to_id": old_instance.assigned_to_id
            }
        except Task.DoesNotExist:
            pass


@receiver(post_save, sender=Task)
def on_task_saved(sender, instance: Task, created, **kwargs):
    """
    Сигнал после сохранения задачи.

    Вызывает сервис уведомлений.
    """
    # Получаем старое значение assigned_to
    old_assigned_to_id = _task_previous_state.get(instance.pk, {}).get("assigned_to_id")

    action = "updated"
    if created:
        action = "created"

    notify_task_change(instance, action, old_assigned_to_id=old_assigned_to_id)

    # Удаляем из кэша
    if instance.pk in _task_previous_state:
        del _task_previous_state[instance.pk]


@receiver(post_delete, sender=Task)
def on_task_deleted(sender, instance: Task, **kwargs):
    """
    Сигнал после удаления задачи.

    Вызывает сервис уведомлений.
    """
    # Отправляем уведомление об удалении
    notify_task_change(instance, "deleted")
