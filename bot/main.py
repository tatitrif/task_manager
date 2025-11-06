"""Telegram bot with API application integration."""

import asyncio
import logging
import os
import re

import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, CommandObject
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
)
logger = logging.getLogger(__name__)

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not BOT_TOKEN:
    raise ValueError("TELEGRAM_TOKEN не задан в .env")

API_AUTH_CONFIRM_URL = (
    os.getenv(
        "API_AUTH_CONFIRM_URL", "http://127.0.0.1:8000/api/auth/telegram/confirm/"
    ).rstrip("/")
    + "/"
)

MSG_START = (
    "Привет! Чтобы привязать аккаунт, перейдите по ссылке из веб-приложения "
    "или отправьте сообщение вида /start <token>, token из веб-приложения"
)

storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=storage)


async def confirm_telegram_link(code: str, message: types.Message):
    """Подтверждает привязку Telegram-аккаунта через API."""
    if not re.fullmatch(r"^[A-Za-z0-9_.-]{8,128}$", code):
        await message.answer("❌ Некорректный формат токена.")
        return

    payload = {"code": code, "telegram_id": message.from_user.id}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                API_AUTH_CONFIRM_URL, json=payload, timeout=10
            ) as resp:
                if not resp.headers.get("Content-Type", "").startswith(
                    "application/json"
                ):
                    logger.error(
                        f"Non-JSON response from API: {await resp.text()[:200]}"
                    )
                    await message.answer(
                        "❌ Сервер вернул ошибку. Обратитесь к администратору."
                    )
                    return

                data = await resp.json()
                logger.debug(f"Response from API: status={resp.status}, data={data}")
                if resp.status == 200:
                    await message.answer("✅ Ваш Telegram-аккаунт успешно привязан!")
                elif resp.status == 400:
                    await message.answer("❌ Неверный или устаревший токен.")
                else:
                    await message.answer(
                        "❌ Не удалось привязать аккаунт. Повторите позже."
                    )

    except TimeoutError:
        logger.warning("Request to API timed out")
        await message.answer("⏰ Превышено время ожидания. Попробуйте позже.")
    except aiohttp.ClientError as e:
        logger.warning(f"HTTP client error: {e}")
        await message.answer("⚠️ Ошибка подключения к серверу.")
    except Exception as e:
        logger.exception(f"Unexpected error in confirm_telegram_link: {e}")
        await message.answer("❌ Произошла внутренняя ошибка.")


@dp.message(CommandStart(deep_link=True))
async def handle_start_link(message: types.Message, command: CommandObject):
    """Обработка deep link /start <token>."""
    code = command.args
    if not code:
        await message.answer(MSG_START)
    else:
        await confirm_telegram_link(code, message)


@dp.message(CommandStart())
async def handle_start(message: types.Message):
    """Обработка обычного /start <token>."""
    parts = message.text.split()
    if len(parts) >= 2:
        await confirm_telegram_link(parts[1], message)
    else:
        await message.answer(MSG_START)


async def main():
    """Запуск бота."""
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
