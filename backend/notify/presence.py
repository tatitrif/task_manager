"""
A module for tracking the online status of users using Redis.

Provides functions for marking users as online/offline and checkin status.
"""

import logging

import redis
from django.conf import settings

logger = logging.getLogger(__name__)

_redis = redis.from_url(settings.REDIS_CHAT_URL)
_KEY = "online_users"


def mark_online(user_id: int) -> None:  # noqa
    logger.debug(f"[REDIS_CHAT] {user_id}{_KEY} mark_online.")
    _redis.sadd(_KEY, user_id)


def mark_offline(user_id: int) -> None:  # noqa
    logger.debug(f"[REDIS_CHAT] {user_id}{_KEY} mark_offline.")
    _redis.srem(_KEY, user_id)


def is_online(user_id: int) -> bool:  # noqa
    logger.debug(f"[REDIS_CHAT] {user_id}{_KEY} is_online.")
    return _redis.sismember(_KEY, user_id)
