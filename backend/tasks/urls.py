"""URL patterns for the project."""

from django.urls import path
from . import views

urlpatterns = [
    # Списки задач
    path("lists/", views.ListTaskListCreateView.as_view(), name="list-list"),
    path("lists/<int:pk>/", views.ListTaskDetailView.as_view(), name="list-detail"),
    # Задачи внутри списка
    path(
        "lists/<int:list_id>/tasks/",
        views.TaskInListView.as_view(),
        name="task-in-list",
    ),
    # Мои назначенные задачи (для Telegram)
    path("tasks/", views.TaskListView.as_view(), name="assigned-tasks"),
    # Управление задачей
    path("tasks/<int:pk>/", views.TaskDetailView.as_view(), name="task-detail"),
    path(
        "tasks/<int:task_id>/complete/",
        views.TaskCompleteView.as_view(),
        name="complete-task",
    ),
]
