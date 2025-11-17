"""Telegram notification sending module."""

import logging

import requests

from config.settings import TELEGRAM_BOT_TOKEN

logger = logging.getLogger(__name__)
API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"


def send_telegram_message(chat_id: int, text: str):
    """
    Отправьте сообщение в чат Telegram.

    Аргументы:     chat_id (int): Идентификатор чата, на который нужно отправить
    сообщение.     text (str): Текст сообщения.
    """
    try:
        requests.post(API_URL, json={"chat_id": chat_id, "text": text}, timeout=15)
    except requests.exceptions.RequestException as e:
        logger.exception(f"Ошибка при отправке сообщения в Telegram: {e}")
    except Exception as e:
        logger.exception(f"Неожиданная ошибка: {e}")
