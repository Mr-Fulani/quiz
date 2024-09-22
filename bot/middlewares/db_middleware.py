from aiogram.types import TelegramObject
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from database.database import get_async_session



class DbSessionMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: TelegramObject, data: dict):
        # Получаем сессию базы данных
        async for session in get_async_session():
            # Добавляем сессию в `data`, чтобы передать её в обработчик
            data['session'] = session
            return await handler(event, data)
