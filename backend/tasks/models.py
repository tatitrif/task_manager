"""Django models for the tasks app."""

from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class BaseModel(models.Model):
    """Абстрактная базовая модель с метками времени создания и обновления."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:  # noqa
        abstract = True


class ListTask(BaseModel):
    """Модель, представляющая список задач."""

    name = models.CharField(max_length=200, unique=True)
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="owned_lists",  # Владелец списка
    )

    def __str__(self):
        """Вернуть название списка задач."""
        return self.name


class Task(BaseModel):
    """Модель, представляющая отдельную задачу."""

    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tasks",  # Исполнитель задачи
    )
    list_tasks = models.ForeignKey(
        ListTask,
        on_delete=models.CASCADE,
        related_name="tasks",  # Список, к которому относится задача
    )
    complete_before = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)

    def __str__(self):
        """Вернуть название задачи."""
        return self.name
