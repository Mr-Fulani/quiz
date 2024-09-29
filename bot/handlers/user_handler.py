from aiogram import types, F
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.inline import topic_keyboard
from bot.services.user_service import add_user_if_not_exists  # Импортируем сервис для добавления пользователя
from config import ALLOWED_USERS



user_router = Router()




@user_router.message(Command("start"))
async def start_command(message: Message):
    await message.answer(
        "Привет! Выберите тему для викторины:",
        reply_markup=topic_keyboard()
    )


@user_router.message(Command("register"))
async def register_user(message: Message, session: AsyncSession):
    # Обработка регистрации пользователя
    await add_user_if_not_exists(message.from_user, session)
    await message.answer("Ваши данные обновлены в системе.")