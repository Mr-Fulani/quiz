import logging
from aiogram import BaseMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker



class DbSessionMiddleware(BaseMiddleware):
    def __init__(self, session_maker: sessionmaker):
        super().__init__()
        self.session_maker = session_maker


    async def __call__(self, handler, event, data):
        # Создаем асинхронную сессию
        async with self.session_maker() as session:
            data['session'] = session
            try:
                # Передаем обработку в хендлер с добавленной сессией
                return await handler(event, data)
            except Exception as e:
                logging.error(f"Ошибка при работе с сессией базы данных: {e}")
                raise
            finally:
                await session.close()