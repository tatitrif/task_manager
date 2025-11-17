"""Middleware module for the backend project."""

from urllib.parse import parse_qs

from asgiref.sync import sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser, User
from django.db import close_old_connections
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import UntypedToken


class JWTAuthMiddleware(BaseMiddleware):
    """Авторизация через JWT из query-параметра WebSocket URL."""

    async def __call__(self, scope, receive, send):  # noqa
        query_string = scope.get("query_string", b"").decode("utf-8")
        query_params = parse_qs(query_string)

        # Извлекаем токен из параметра 'token'
        # parse_qs возвращает список значений, берем первое
        token = query_params.get("token", [None])[0]

        if token:
            try:
                # Проверяется подпись, срок действия и тип токена.
                untyped_token = UntypedToken(token)
                # Извлекаем user_id из полезной нагрузки токена
                user_id = untyped_token["user_id"]
                # Асинхронно получаем пользователя из базы данных
                scope["user"] = await sync_to_async(User.objects.get)(id=user_id)
            except (InvalidToken, TokenError, KeyError, User.DoesNotExist):
                scope["user"] = AnonymousUser()
        else:
            # Если токен не был предоставлен в URL, пользователь анонимен.
            scope["user"] = AnonymousUser()

        # Закрываем старые соединения с базой данных.
        # Это критически важно для предотвращения утечек соединений в долгоживущих WebSocket-соединениях.
        # Django по умолчанию не закрывает соединения после завершения HTTP-запроса, но для WebSocket это необходимо.
        close_old_connections()

        # Передаем управление следующему уровню в цепочке middleware или самому Consumer'у.
        return await super().__call__(scope, receive, send)
