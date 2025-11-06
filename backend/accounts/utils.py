"""Telegram integration utilities for secure one-time token linking."""

import uuid

from django.conf import settings
from django.core.cache import cache

TELEGRAM_LINK_TOKEN_EXPIRE = getattr(settings, "TELEGRAM_LINK_TOKEN_EXPIRE", 600)


def generate_telegram_token(
    user_id: int, expire: int = TELEGRAM_LINK_TOKEN_EXPIRE
) -> str:
    """Создаёт одноразовый токен для привязки Telegram-аккаунта."""
    token = uuid.uuid4().hex  # 32 символа, только [0-9a-f] ограничение deep_link
    cache.set(f"tg_token:{token}", user_id, timeout=expire)
    return token


def verify_telegram_token(token: str) -> int | None:
    """Проверяет токен и возвращает ID пользователя, если валиден и не истёк."""
    user_id = cache.get(f"tg_token:{token}")
    if user_id:
        cache.delete(f"tg_token:{token}")  # удаляем одноразовый токен
        return int(user_id)
    return None
