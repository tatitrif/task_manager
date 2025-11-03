"""URL patterns for the project."""

from django.urls import path

from . import views

urlpatterns = [
    path(
        "lists/", views.ListTaskListCreateView.as_view(), name="list-task-list-create"
    ),
    path(
        "lists/<int:pk>/", views.ListTaskDetailView.as_view(), name="list-task-detail"
    ),
    path(
        "lists/<int:list_id>/tasks/",
        views.ListTaskTasksView.as_view(),
        name="list-task-tasks",
    ),
    path("tasks/", views.TaskCreateView.as_view(), name="task-create"),
    path("tasks/<int:pk>/", views.TaskUpdateView.as_view(), name="task-update"),
]
