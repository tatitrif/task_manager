"""Django models for the tasks app."""

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

User = get_user_model()


class BaseModel(models.Model):
    """Абстрактная модель, содержащая общие поля."""

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:  # noqa
        abstract = True


class ListTask(BaseModel):
    """Модель, представляющая список задач."""

    name = models.CharField(max_length=200, unique=True, verbose_name="Название списка")
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="owned_lists",  # Владелец списка
        verbose_name="Владелец списка",
    )

    class Meta:  # noqa
        indexes = [
            models.Index(fields=["owner"]),  # Индекс для фильтрации по владельцу
        ]
        verbose_name = "Список задач"
        verbose_name_plural = "Списки задач"
        ordering = ["-created_at"]

    def __str__(self):
        """Возвращает строковое представление списка задач."""
        return self.name


class TaskStatus(models.TextChoices):
    """Модель статусов задач."""

    PENDING = "Pending", "Ожидает"
    IN_PROGRESS = "In Progress", "В процессе"
    COMPLETED = "Completed", "Выполнена"
    OVERDUE = "Overdue", "Просрочена"


class Task(BaseModel):
    """Модель, представляющая отдельную задачу."""

    name = models.CharField(max_length=200, verbose_name="Название задачи")
    description = models.TextField(blank=True, verbose_name="Описание")
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tasks",
        verbose_name="Назначена пользователю",
    )
    list_tasks = models.ForeignKey(
        ListTask,
        on_delete=models.CASCADE,
        related_name="tasks",  # Список, к которому относится задача
        db_index=True,  # Индекс для ускорения фильтрации по списку
        verbose_name="Список задач",
    )
    complete_before = models.DateTimeField(
        null=True, blank=True, verbose_name="Выполнить до"
    )

    status = models.CharField(
        max_length=20,
        choices=TaskStatus,
        default=TaskStatus.PENDING,
        verbose_name="Статус задачи",
    )

    class Meta:  # noqa
        verbose_name = "Задача"
        verbose_name_plural = "Задачи"
        ordering = ["-created_at"]
        unique_together = ["name", "list_tasks"]

    def __str__(self):
        """Возвращает строковое представление задачи."""
        return self.name

    def save(self, *args, **kwargs):
        """Автоматически обновляем статус."""
        # Если задача назначена
        if self.assigned_to and self.status == TaskStatus.PENDING:
            self.status = TaskStatus.IN_PROGRESS
        super().save(*args, **kwargs)

    def mark_completed(self):
        """Помечает задачу как выполненную."""
        if self.status == TaskStatus.IN_PROGRESS:
            self.status = TaskStatus.COMPLETED
            self.save(update_fields=["status", "updated_at"])
            return True
        return False

    def mark_overdue(self):
        """Помечает задачу как просроченную."""
        if (
            self.complete_before
            and self.complete_before < timezone.now()
            and self.status not in [TaskStatus.COMPLETED, TaskStatus.OVERDUE]
        ):
            self.status = TaskStatus.OVERDUE
            self.save(update_fields=["status", "updated_at"])
            return True
        return False

    @property
    def is_completed(self):
        """Возвращает True, если задача выполнена."""
        return self.status == TaskStatus.COMPLETED
