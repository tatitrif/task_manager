"""Django REST Framework views for the tasks app."""

from django.db.models import Q
from rest_framework import generics, status
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .mixins import BaseUserSecureView
from .models import ListTask, Task, TaskStatus
from .serializers import ListTaskSerializer, TaskSerializer


# GET /api/lists/ — Список всех списков задач
# POST /api/lists/ — Создание нового списка задач
class ListTaskListCreateView(BaseUserSecureView, generics.ListCreateAPIView):
    """Получение списка задач или создание нового."""

    serializer_class = ListTaskSerializer

    def get_queryset(self):
        """Возвращает список задач, принадлежащих пользователю."""
        return self.get_user_queryset(ListTask)

    def perform_create(self, serializer):
        """Сохраняет новый список задач с текущим пользователем."""  # noqa
        serializer.save(owner=self.request.user)


# GET/PUT/PATCH /api/lists/<id>/ — работа со списком.
class ListTaskDetailView(BaseUserSecureView, generics.RetrieveUpdateAPIView):
    """Получение и обновление конкретного списка задач."""

    serializer_class = ListTaskSerializer

    def get_queryset(self):
        """Возвращает список задач, принадлежащий пользователю."""
        return self.get_user_queryset(ListTask)


# GET /api/lists/<list_id>/tasks/ — задачи в списке
# POST /api/lists/<list_id>/tasks/ — создать задачу в списке.
class TaskInListView(BaseUserSecureView, generics.ListCreateAPIView):
    """Получение задач в списке или создание новой задачи в списке."""

    serializer_class = TaskSerializer

    def get_queryset(self):
        """Возвращает задачи, связанные с указанным списком задач."""
        list_task = self.get_object_user_safe(ListTask, id=self.kwargs["list_id"])
        return Task.objects.filter(list_tasks=list_task).select_related("list_tasks")

    def perform_create(self, serializer):
        """Сохраняет новую задачу, привязанную к списку задач."""
        list_task = self.get_object_user_safe(ListTask, id=self.kwargs["list_id"])
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
            Q(list_tasks__owner=user) | Q(assigned_to=user)
        ).select_related("list_tasks", "assigned_to")


# GET /api/tasks/ — все задачи, назначенные пользователю.
class TaskListView(BaseUserSecureView, generics.ListAPIView):
    """Получение списка задач, назначенных пользователю."""

    serializer_class = TaskSerializer

    def get_queryset(self):
        """Возвращает задачи, назначенные текущему пользователю."""
        return Task.objects.filter(assigned_to=self.request.user).select_related(
            "list_tasks", "assigned_to"
        )


# POST /api/tasks/<task_id>/complete/ — завершить задачу.
class TaskCompleteView(BaseUserSecureView, generics.ListAPIView):
    """Отметка задачи как выполненной."""

    def post(self, request, task_id):
        """Отмечает задачу как выполненную."""
        user = self.request.user
        task_qs = Task.objects.filter(
            Q(list_tasks__owner=user) | Q(assigned_to=user)
        ).select_related("list_tasks", "assigned_to")
        task = get_object_or_404(task_qs, id=task_id)

        # Проверяем активность
        if not task.status == TaskStatus.IN_PROGRESS:
            return Response(
                {"detail": "Task is expired and cannot be completed"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Отмечаем как выполненную, если ещё не завершена
        if task.mark_completed():
            return Response(
                {"detail": "Task marked as complete"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"detail": "Task was already completed or could not be completed"},
            status=status.HTTP_400_BAD_REQUEST,
        )
