"""Django admin configuration for the tasks app."""

from django.contrib import admin
from django.db import models

from .models import ListTask, Task


class TaskInline(admin.TabularInline):
    """Встроенный админ для модели Task внутри админки ListTask."""

    model = Task
    extra = 1
    fields = ("name", "assigned_to", "complete_before", "status")

    # def get_queryset(self, request):
    #     """Оптимизация для задач в инлайне."""
    #     qs = super().get_queryset(request)
    #     return qs.select_related("assigned_to")


def display_task_ids(obj):
    """Возвращает строку с первыми N ID задач и общим количеством для отображения."""
    task_ids = obj.tasks.values_list("id", flat=True)
    total_count = len(task_ids)
    if total_count == 0:
        return "No tasks"
    # Берём первые N IDs
    count_ids = 3
    displayed_ids = list(task_ids[:count_ids])
    ids_str = ", ".join(map(str, displayed_ids))
    if total_count > count_ids:
        return f"{ids_str}... ({total_count})"
    else:
        return f"{ids_str} ({total_count})"


@admin.register(ListTask)
class ListTasksAdmin(admin.ModelAdmin):
    """Интерфейс администратора для модели ListTask."""

    save_as = True
    save_on_top = True
    list_display = (
        "id",
        "name",
        "owner",
        "updated_at",
        "task_summary",
    )
    search_fields = ("name",)
    readonly_fields = ("updated_at",)
    list_select_related = ("owner",)
    inlines = [TaskInline]

    def get_queryset(self, request):
        """Оптимизировать набор запросов, чтобы включить количество задач."""
        queryset = super().get_queryset(request)
        return queryset.annotate(task_count=models.Count("tasks"))

    @admin.display(
        description="Tasks (ID)",
        ordering="task_count",
    )
    def task_summary(self, obj):
        """Отображение сводки по ID задач и их общему количеству."""
        return display_task_ids(obj)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """Интерфейс администратора для модели Task."""

    save_as = True
    save_on_top = True
    list_display = (
        "id",
        "name",
        "list_tasks",
        "assigned_to",
        "complete_before",
        "status",
        "updated_at",
    )
    list_filter = ("status", "list_tasks", "assigned_to")
    list_editable = (
        "status",
        "assigned_to",
    )
    search_fields = ("name",)
    readonly_fields = (
        "created_at",
        "updated_at",
    )
    date_hierarchy = "complete_before"
    list_select_related = ("list_tasks", "assigned_to")
