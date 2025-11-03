"""Django REST Framework serializers for the tasks app."""

from django.contrib.auth.models import User
from rest_framework import serializers

from .models import ListTask, Task


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для модели User."""

    class Meta:  # noqa
        model = User
        fields = ["id", "username"]


class ListTaskSerializer(serializers.ModelSerializer):
    """Сериализатор для модели ListTask."""

    owner = UserSerializer(read_only=True)

    class Meta:  # noqa
        model = ListTask
        fields = "__all__"
        read_only_fields = ["owner", "created_at", "updated_at"]


class TaskForListSerializer(serializers.ModelSerializer):
    """Сериализатор для задач, вложенных в ListTask."""

    assigned_to = UserSerializer(read_only=True)

    class Meta:  # noqa
        model = Task
        fields = [
            "id",
            "name",
            "assigned_to",
            "complete_before",
            "is_completed",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["assigned_to", "created_at", "updated_at"]


class ListTaskWithTasksSerializer(serializers.ModelSerializer):
    """Сериализатор для ListTask, включающий список задач."""

    owner = UserSerializer(read_only=True)
    tasks = TaskForListSerializer(many=True, read_only=True)

    class Meta:  # noqa
        model = ListTask
        fields = "__all__"
        read_only_fields = ["owner", "created_at", "updated_at"]


class TaskSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Task."""

    assigned_to = UserSerializer(read_only=True)

    class Meta:  # noqa
        model = Task
        fields = "__all__"
        read_only_fields = ["assigned_to", "created_at", "updated_at"]
