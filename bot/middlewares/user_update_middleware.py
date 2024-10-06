import logging
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from database.database import add_user_if_not_exists



class UserUpdateMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data: dict):
        session: AsyncSession = data['session']  # Получаем сессию из контекста

        try:
            # Получаем данные о пользователе из события
            user_data = event.from_user
            logging.info(
                f"Данные пользователя из события: ID={user_data.id},"
                f" Username={user_data.username}, Language={user_data.language_code}")

            if user_data:
                # Обновляем информацию о пользователе в базе данных
                await add_user_if_not_exists(user_data, session)
        except Exception as e:
            # Логируем ошибку, если возникла проблема с обновлением данных
            logging.error(f"Ошибка при обновлении данных пользователя {event.from_user.id}: {e}")

        # Передаем управление следующему middleware или хендлеру
        return await handler(event, data)