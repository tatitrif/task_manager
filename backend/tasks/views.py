"""Django REST Framework views for the tasks app."""

import django.db.models as models
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .models import ListTask, Task
from .serializers import ListTaskSerializer, TaskSerializer, ListTaskWithTasksSerializer


class ListTaskListCreateView(generics.ListCreateAPIView):
    """Представление для получения списка ListTask и создания нового."""

    serializer_class = ListTaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Получить набор запросов, отфильтрованный по владельцу."""
        return ListTask.objects.filter(owner=self.request.user).select_related("owner")

    def perform_create(self, serializer):
        """Сохранить новый экземпляр ListTask с владельцем."""
        serializer.save(owner=self.request.user)


class ListTaskDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Представление для получения, обновления и удаления конкретного ListTask."""

    queryset = ListTask.objects.all()
    serializer_class = ListTaskWithTasksSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Получить набор запросов для ListTask, к которым можно добавлять задачи."""
        return (
            ListTask.objects.filter(owner=self.request.user)
            .select_related("owner")
            .prefetch_related("tasks")
        )


class ListTaskTasksView(generics.ListAPIView):
    """Представление для получения списка задач для конкретного ListTask."""

    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Получить набор запросов задач, отфильтрованный по ID списка."""
        list_id = self.kwargs["list_id"]
        return Task.objects.filter(list_tasks_id=list_id).select_related("assigned_to")


class TaskCreateView(generics.CreateAPIView):
    """Представление для создания новой задачи."""

    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Получить набор запросов для ListTask, к которым можно добавлять задачи."""
        return ListTask.objects.filter(owner=self.request.user).select_related("owner")


class TaskUpdateView(generics.RetrieveUpdateAPIView):
    """Представление для получения и обновления существующей задачи."""

    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Получить набор запросов задач, к которым у пользователя есть доступ."""
        # владелец списка или назначенный
        return Task.objects.filter(
            models.Q(list_tasks__owner=self.request.user)
            | models.Q(assigned_to=self.request.user)
        ).select_related("list_tasks__owner", "assigned_to")
