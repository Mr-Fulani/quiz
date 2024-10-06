import logging
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from database.database import add_user_if_not_exists


class DbSessionMiddleware(BaseMiddleware):
    def __init__(self, session_maker):
        self.session_maker = session_maker

    async def __call__(self, handler, event, data: dict):
        async with self.session_maker() as session:
            data['session'] = session
            try:
                if isinstance(event, (Message, CallbackQuery)):
                    user = event.from_user
                    logging.info(f"Полные данные пользователя: {user.model_dump_json(indent=2)}")

                    user_data = {
                        'id': user.id,
                        'username': user.username,
                        'language_code': user.language_code,
                        'is_premium': user.is_premium,
                        'added_to_attachment_menu': user.added_to_attachment_menu,
                    }
                    logging.info(f"Извлеченные данные пользователя: {user_data}")

                    logging.info(f"Получено событие от пользователя: {user.id}")
                    await add_user_if_not_exists(user, session)
                else:
                    logging.warning(f"Неизвестный тип события: {type(event)}")
            except Exception as e:
                logging.error(f"Ошибка при обработке данных пользователя: {e}")

            return await handler(event, data)