"""Django REST Framework views for the tasks app."""

from django.db import models
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from tasks.models import ListTask, Task
from .serializers import ListTaskSerializer, TaskSerializer


# GET /api/lists/ — мои списки
# POST /api/lists/ — создать список.
class ListTaskListCreateView(generics.ListCreateAPIView):
    """Получение списка задач или создание нового."""

    serializer_class = ListTaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Возвращает список задач, принадлежащих пользователю."""
        return ListTask.objects.filter(owner=self.request.user).select_related("owner")

    def perform_create(self, serializer):
        """Сохраняет новый список задач с текущим пользователем."""
        serializer.save(owner=self.request.user)


#  GET/PUT/PATCH /api/lists/<id>/ — работа со списком.
class ListTaskDetailView(generics.RetrieveUpdateAPIView):
    """Получение и обновление конкретного списка задач."""

    serializer_class = ListTaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Возвращает список задач, принадлежащий пользователю."""
        return ListTask.objects.filter(owner=self.request.user).select_related("owner")


#  GET /api/lists/<list_id>/tasks/ — задачи в списке
#  POST /api/lists/<list_id>/tasks/ — создать задачу в списке.
class TaskInListView(generics.ListCreateAPIView):
    """Получение задач в списке или создание новой задачи в списке."""

    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Возвращает задачи, связанные с указанным списком задач."""
        list_id = self.kwargs["list_id"]
        list_task = get_object_or_404(ListTask, id=list_id, owner=self.request.user)
        return Task.objects.filter(list_tasks=list_task).select_related("list_tasks")

    def perform_create(self, serializer):
        """Сохраняет новую задачу, привязанную к списку задач."""
        list_id = self.kwargs["list_id"]
        list_task = get_object_or_404(ListTask, id=list_id, owner=self.request.user)
        serializer.save(list_tasks=list_task)


# GET/PUT/PATCH /api/tasks/<id>/"
class TaskDetailView(generics.RetrieveUpdateAPIView):
    """Получение, обновление и частичное обновление задачи."""

    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Возвращает задачи, доступные пользователю."""
        user = self.request.user
        # Владелец списка ИЛИ исполнитель задачи
        return Task.objects.filter(
            models.Q(list_tasks__owner=user) | models.Q(assigned_to=user)
        ).select_related("list_tasks", "assigned_to")


# GET /api/tasks/ — все задачи, назначенные пользователю.
class TaskListView(generics.ListAPIView):
    """Получение списка задач, назначенных пользователю."""

    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Возвращает задачи, назначенные текущему пользователю."""
        return Task.objects.filter(assigned_to=self.request.user).select_related(
            "assigned_to"
        )


# POST /api/tasks/<task_id>/complete/ — завершить задачу.
class TaskCompleteView(generics.GenericAPIView):
    """Отметка задачи как выполненной."""

    permission_classes = [IsAuthenticated]

    def post(self, request, task_id):
        """Отмечает задачу как выполненную."""
        task = get_object_or_404(Task, id=task_id, assigned_to=request.user)
        task.is_completed = True
        task.save(update_fields=["is_completed"])
        return Response(
            {"detail": "Task marked as complete"}, status=status.HTTP_200_OK
        )
