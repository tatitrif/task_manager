"""Telegram integration utilities for secure one-time token linking."""

import logging

import itsdangerous
from django.conf import settings

TELEGRAM_LINK_TOKEN_EXPIRE = getattr(settings, "TELEGRAM_LINK_TOKEN_EXPIRE", 600)

logger = logging.getLogger(__name__)
_serializer = itsdangerous.URLSafeTimedSerializer(
    settings.SECRET_KEY, salt="telegram-link"
)


def generate_telegram_token(user_id: int) -> str:
    """Создаёт одноразовый токен для привязки Telegram-аккаунта."""
    return _serializer.dumps({"user_id": user_id})


def verify_telegram_token(
    token: str, max_age: int = TELEGRAM_LINK_TOKEN_EXPIRE
) -> int | None:
    """Проверяет токен и возвращает ID пользователя, если валиден и не истёк."""
    try:
        data = _serializer.loads(token, max_age=max_age)
        user_id = data.get("user_id")
        return int(user_id) if user_id else None
    except itsdangerous.BadSignature:
        logger.warning("Invalid or tampered Telegram link token received")
        return None
    except Exception as e:
        logger.exception(f"Unexpected error during Telegram token verification: {e}")
        return None
