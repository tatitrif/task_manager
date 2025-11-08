"""Telegram bot with API application integration."""

import asyncio
import logging
import os
import re

import aiohttp
from aiogram import Bot, Dispatcher, types, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeDefault
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/api/")
API_AUTH_CONFIRM_URL = API_BASE_URL.rstrip("/") + "/auth/telegram/confirm/"
API_REFRESH_URL = API_BASE_URL.rstrip("/") + "/auth/token/refresh/"
API_TASKS_URL = API_BASE_URL.rstrip("/") + "/tasks/"

MSG_START = (
    "Привет! Чтобы привязать аккаунт, перейдите по ссылке из веб-приложения "
    "или отправьте сообщение вида /start <token>, token из веб-приложения"
)

DEFAULT_COMMANDS = [
    BotCommand(command="start", description="Старт"),
]

router = Router()


async def refresh_access_token(refresh_token: str) -> str | None:
    """Обновляет access-токен через refresh."""
    payload = {"refresh": refresh_token}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                API_REFRESH_URL,
                json=payload,
                timeout=10,
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("access")
                logger.warning(f"Token refresh failed: {resp.status}")
    except Exception as e:
        logger.exception(f"Token refresh error: {e}")
    return


async def confirm_telegram_link(code: str, message: types.Message, state: FSMContext):
    """Подтверждает привязку Telegram-аккаунта через API."""
    if not code or not re.fullmatch(r"[0-9a-f]{32}", code, flags=re.IGNORECASE):
        await message.answer("❌ Некорректный формат токена.")
        return

    payload = {"code": code, "telegram_id": message.from_user.id}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                API_AUTH_CONFIRM_URL, json=payload, timeout=10
            ) as resp:
                logger.info(f"API response status: {resp.status}")
                if not resp.headers.get("Content-Type", "").startswith(
                    "application/json"
                ):
                    await message.answer("❌ Сервер вернул ошибку (не JSON).")
                    return

                data = await resp.json()
                if resp.status in {400, 409, 429}:
                    await message.answer(data.get("error") or "Ошибка подтверждения.")
                    return
                if resp.status != 200:
                    await message.answer(f"❌ Ошибка. Код {resp.status}")
                    return

                access = data.get("access")
                refresh = data.get("refresh")
                if not access or not refresh:
                    await message.answer("❌ JWT токены не получены.")
                    return

                await state.update_data(access=access, refresh=refresh)
                await message.answer(
                    "✅ Аккаунт успешно привязан!\n\n"
                    "Теперь вы можете использовать команду /tasks, чтобы посмотреть свои задачи."
                )
    except asyncio.exceptions.TimeoutError:
        await message.answer("⏰ Превышено время ожидания. Попробуйте позже.")
    except aiohttp.ClientError:
        await message.answer("⚠️ Ошибка подключения к серверу.")
    except Exception as e:
        logger.exception(e)
        await message.answer("❌ Внутренняя ошибка.")


@router.message(CommandStart())
async def handle_start(
    message: types.Message, command: CommandObject, state: FSMContext
):
    """Обрабатывает /start и /start <token>."""
    code = command.args or (
        message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None
    )
    if not code:
        await message.answer(MSG_START)
        return
    await confirm_telegram_link(code, message, state)


async def fetch_tasks(access: str) -> dict[list[dict]] | None:
    """Получает список задач по access токену."""
    headers = {"Authorization": f"Bearer {access}"}
    async with aiohttp.ClientSession() as session:
        async with session.get(API_TASKS_URL, headers=headers, timeout=10) as resp:
            if resp.status == 200:
                return await resp.json()
            elif resp.status in {401, 403}:
                return
            else:
                logger.error(f"Error fetching tasks: {resp.status} {await resp.text()}")
                return


@router.message(Command("tasks"))
async def tasks_list(message: types.Message, state: FSMContext):
    """Отображает список задач пользователя."""
    data = await state.get_data()
    access, refresh = data.get("access"), data.get("refresh")

    if not access:
        await message.answer(
            "❌ Аккаунт не привязан. Используйте /start <token> сначала."
        )
        return

    tasks_data = await fetch_tasks(access)
    if tasks_data is None and refresh:
        # access просрочен — пробуем обновить
        new_access = await refresh_access_token(refresh)
        if new_access:
            await state.update_data(access=new_access)
            tasks_data = await fetch_tasks(new_access)

    logger.debug(f"tasks_data: {tasks_data}")

    if tasks_data is None:
        await message.answer("🔒 Авторизация истекла. Повторите /start <token>.")
        return

    tasks = tasks_data.get("results", [])

    if not tasks:
        await message.answer("✅ У вас нет назначенных задач.")
        return

    logger.debug(f"tasks_list: {tasks_list}")

    text = "*Ваши задачи:*\n\n" + "\n".join(
        f"{'✅' if t.get('is_completed') else '❌'} [{t.get('list_name', '—')}] #{t.get('id')}: {t.get('name')}"
        for t in tasks
    )
    buttons = [
        InlineKeyboardButton(text=t.get("name"), callback_data=f"done:{t.get('id')}")
        for t in tasks
        if not t.get("is_completed")
    ]
    kb = (
        InlineKeyboardMarkup(
            inline_keyboard=[buttons[i : i + 2] for i in range(0, len(buttons), 2)]  # noqa
        )
        if buttons
        else None
    )

    await message.answer(text, reply_markup=kb)


@router.callback_query(lambda c: c.data and c.data.startswith("done:"))
async def complete_task(callback: types.CallbackQuery, state: FSMContext):
    """Отмечает задачу выполненной."""
    task_id = callback.data.split(":", 1)[1]
    data = await state.get_data()
    access, refresh = data.get("access"), data.get("refresh")

    if not access:
        await callback.message.answer(
            "❌ Аккаунт не привязан. Используйте /start <token> сначала."
        )
        return

    url = f"{API_TASKS_URL}{task_id}/complete/"

    async def complete(access_token: str) -> bool:
        headers = {"Authorization": f"Bearer {access_token}"}
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(url, timeout=10) as resp:
                if resp.status == 200:
                    logger.info(f"✅ Task {task_id} marked as complete")
                    return True

                # читаем ответ для отладки
                detail = (await resp.json()).get("detail", "Неизвестная ошибка")
                logger.warning(f"⚠️ Не удалось завершить задачу {task_id}: {detail}")
                return False

    ok = await complete(access)
    if not ok and refresh:
        new_access = await refresh_access_token(refresh)
        if new_access:
            await state.update_data(access=new_access)
            ok = await complete(new_access)

    if ok:
        await callback.message.edit_text("✅ Задача выполнена!")
    else:
        await callback.message.answer(
            "⚠️ Ошибка при завершении задачи. Возможно, авторизация истекла."
        )


async def on_startup(bot: Bot):
    """Вызывается при запуске бота."""
    logging.info("Starting bot... Setting up default commands.")
    await bot.set_my_commands(DEFAULT_COMMANDS, BotCommandScopeDefault())


async def on_shutdown(bot: Bot):
    """Вызывается при остановке бота."""
    logging.info("Bot stopping... Removing the default commands.")
    await bot.delete_my_commands(BotCommandScopeDefault())


async def main():
    """Запуск бота."""
    logging.basicConfig(
        level=logging.DEBUG,
        format="[%(asctime)s] - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
    )

    if not BOT_TOKEN:
        raise ValueError("TELEGRAM_TOKEN не задан в .env")

    bot = Bot(
        token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
    )
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Регистрируем функции на события запуска и остановки бота
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Подключаем роутер
    dp.include_router(router)

    # Запускаем
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
