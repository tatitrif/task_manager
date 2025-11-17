"""
The module provides base classes and admixtures for task representations.

- Проверяет авторизацию.
- Фильтрует queryset по пользователю.
- Реализует оптимистичную блокировку через `updated_at`.
- Поддерживает пагинацию, если задан `pagination_class`.
"""

from django.db import models
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_datetime
from rest_framework import generics, status
from rest_framework.exceptions import APIException
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


class ConflictError(APIException):
    """Ошибка при конфликте версий (оптимистичная блокировка)."""

    status_code = status.HTTP_409_CONFLICT
    default_detail = "Конфликт обновления: данные были изменены другим пользователем."
    default_code = "conflict"


class BaseUserSecureView(generics.GenericAPIView):
    """Базовый класс для всех вью."""

    permission_classes = [IsAuthenticated]
    updated_at_field = "updated_at"

    def get_user_queryset(self, model):
        """Возвращает queryset, доступный текущему пользователю."""
        user = self.request.user

        if model.__name__ == "ListTask":
            return model.objects.filter(owner=user).select_related("owner")

        if model.__name__ == "Task":
            return model.objects.filter(
                models.Q(list_tasks__owner=user) | models.Q(assigned_to=user)
            ).select_related("list_tasks", "assigned_to")

        return model.objects.none()

    def get_object_user_safe(self, model, **kwargs):
        """Безопасно получает объект, доступный пользователю."""
        qs = self.get_user_queryset(model)
        return get_object_or_404(qs, **kwargs)

    def perform_update(self, serializer):
        """Optimistic lock."""
        instance = self.get_object()
        client_updated_at = self.request.data.get(self.updated_at_field)

        if not client_updated_at:
            raise ConflictError(
                f"Поле '{self.updated_at_field}' обязательно для обновления."
            )

        client_ts = parse_datetime(client_updated_at)
        if not client_ts:
            raise ConflictError(f"Некорректный формат поля '{self.updated_at_field}'.")

        instance_ts = getattr(instance, self.updated_at_field)
        if instance_ts != client_ts:
            raise ConflictError("Объект уже был изменён другим пользователем.")

        serializer.save()

    def paginate_and_respond(self, queryset, serializer_class):
        """Применяет пагинацию (если задана) и возвращает Response."""
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = serializer_class(queryset, many=True)
        return Response(serializer.data)
