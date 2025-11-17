"""URL patterns for the project."""

from django.urls import path

from . import views

urlpatterns = [
    # Списки задач
    # GET /api/lists/ — Список всех списков задач
    # POST /api/lists/ — Создание нового списка задач
    path("lists/", views.ListTaskListCreateView.as_view(), name="list-list"),
    # GET/PUT/PATCH /api/lists/<id>/ — работа со списком.
    path("lists/<int:pk>/", views.ListTaskDetailView.as_view(), name="list-detail"),
    # Задачи внутри списка
    # GET /api/lists/<list_id>/tasks/ — задачи в списке
    # POST /api/lists/<list_id>/tasks/ — создать задачу в списке.
    path(
        "lists/<int:list_id>/tasks/",
        views.TaskInListView.as_view(),
        name="task-in-list",
    ),
    # Задачи
    # GET /api/tasks/ — все задачи, назначенные пользователю.
    path("tasks/", views.TaskListView.as_view(), name="assigned-tasks"),
    # GET/PUT/PATCH /api/tasks/<id>/"
    path("tasks/<int:pk>/", views.TaskDetailView.as_view(), name="task-detail"),
    # POST /api/tasks/<task_id>/complete/
    path(
        "tasks/<int:task_id>/complete/",
        views.TaskCompleteView.as_view(),
        name="complete-task",
    ),
]
