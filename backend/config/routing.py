"""The routing module."""

from django.urls import path

from notify import consumers

websocket_urlpatterns = [
    path("ws/tasks/", consumers.TaskConsumer.as_asgi(), name="task-websocket"),
]
