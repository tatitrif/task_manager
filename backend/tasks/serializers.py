"""Django REST Framework serializers for the tasks app."""

from rest_framework import serializers

from .models import ListTask, Task


class ListTaskSerializer(serializers.ModelSerializer):
    """Сериализатор для модели ListTask."""

    owner_username = serializers.CharField(source="owner.username", read_only=True)

    class Meta:  # noqa
        model = ListTask
        fields = ["id", "name", "owner_username", "updated_at"]
        read_only_fields = ["owner"]


class TaskSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Task."""

    list_name = serializers.CharField(source="list_tasks.name", read_only=True)
    assignee_name = serializers.CharField(source="assigned_to.username", read_only=True)

    class Meta:  # noqa
        model = Task
        fields = [
            "id",
            "name",
            "description",
            "list_name",
            "assignee_name",
            "assigned_to",
            "complete_before",
            "status",
            "is_completed",
            "updated_at",
        ]
