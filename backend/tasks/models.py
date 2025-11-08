"""Django models for the tasks app."""

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

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

    class Meta:  # noqa
        indexes = [
            models.Index(fields=["owner"]),  # Индекс для фильтрации по владельцу
        ]

    def __str__(self):
        """Возвращает строковое представление списка задач."""
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
        db_index=True,  # Индекс для ускорения фильтрации по списку
    )
    complete_before = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)

    class Meta:  # noqa
        indexes = [
            models.Index(fields=["list_tasks", "is_completed"]),
            models.Index(fields=["assigned_to", "is_completed"]),
        ]

    def __str__(self):
        """Возвращает строковое представление задачи."""
        return self.name

    def is_active(self):
        """Проверяет, не просрочена ли задача."""
        return self.complete_before is None or self.complete_before >= timezone.now()

    def mark_completed(self):
        """Помечает задачу как выполненную."""
        if not self.is_completed and self.is_active():
            self.is_completed = True
            self.save(update_fields=["is_completed"])
            return True
        return False
