"""WebSocket consumer for handling real-time task updates and notifications."""

import json
import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from .presence import mark_online, mark_offline

logger = logging.getLogger(__name__)


class TaskConsumer(AsyncWebsocketConsumer):
    """Обрабатывает WebSocket-соединения для обновлений в реальном времени."""

    async def connect(self):
        """Обработка подключения клиента."""
        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            await self.close(code=4001, reason="Неавторизованный пользователь.")
            return
        self.user = user

        # Создаём имя группы для приватных сообщений пользователя
        self.group_name = f"user_{user.id}"
        # Присоединяем канал к группе
        await self.channel_layer.group_add(self.group_name, self.channel_name)

        # Принимаем соединение
        await self.accept()

        # Отмечаем пользователя как онлайн
        await database_sync_to_async(mark_online)(user.id)
        # await self.send(json.dumps({"message": f"{user.username} присоединилась."}))
        logger.info(f"[WS] {user} connected to {self.group_name}")

    async def disconnect(self, close_code):
        """Обработка отключения клиента."""
        user = self.scope.get("user")
        if user and user.is_authenticated:
            # Покидаем группу
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name,
            )
            # Отмечаем пользователя как офлайн
            await database_sync_to_async(mark_offline)(user.id)
            # await self.send(json.dumps({"message": f"{user.username} disconnected."}))
            logger.info(f"[WS] {user} disconnected")

    async def receive(self, text_data=None, bytes_data=None):
        """Handle incoming messages from the client."""
        if not text_data:
            return

        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send_json({"error": "Invalid JSON"})
            return

        logger.debug(f"[WS][recv] User={self.user.id} Data={data}")

    async def ws_event(self, event):
        """Вызывает обработчик, когда другой код вызывает group_send."""
        payload = event.get("data", {})

        logger.debug(f"[WS][send] to user={self.user.id} Payload={payload}")

        await self.send_json(payload)

    async def send_json(self, content: dict):
        """Safe wrapper to send JSON over WebSocket."""
        await self.send(text_data=json.dumps(content))
