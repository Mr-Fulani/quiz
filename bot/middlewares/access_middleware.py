import logging
from aiogram import BaseMiddleware
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from database.database import add_user_if_not_exists




class ChatAccessMiddleware(BaseMiddleware):
    def __init__(self, allowed_users, session_maker):
        super().__init__()
        self.allowed_users = allowed_users
        self.session_maker = session_maker

    async def __call__(self, handler, event, data):
        logging.info(f"Получено сообщение от пользователя {event.from_user.id} в чате {event.chat.id} ({event.chat.type})")

        if isinstance(event, Message):
            if event.chat.type != 'private' or event.from_user.id not in self.allowed_users:
                logging.info(f"Сообщение отклонено: {'Не личный чат' if event.chat.type != 'private' else 'Пользователь не разрешен'}")
                return

            try:
                # Используем контекстный менеджер для создания новой сессии
                async with self.session_maker() as session:
                    await add_user_if_not_exists(event.from_user, session)
                    logging.info(f"Пользователь {event.from_user.id} добавлен в базу данных (если не существовал ранее).")
            except Exception as e:
                logging.error(f"Ошибка при добавлении пользователя {event.from_user.id} в базу данных: {e}")

        logging.info("Сообщение принято для обработки")
        return await handler(event, data)