import asyncio
import logging
from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import Message
from bot.handlers.group_quiz_handler import group_publisher_router
from bot.handlers.quiz import quiz_router
from bot.handlers.user_handler import user_router
from bot.keyboards.inline import topic_keyboard
from bot.middlewares.db_middleware import DbSessionMiddleware
from bot.middlewares.access_middleware import ChatAccessMiddleware
from config import BOT_TOKEN, ALLOWED_USERS
from database.database import async_sessionmaker  # Импортируем фабрику асинхронных сессий


# Создание нового роутера для команды /start
start_router = Router()


@start_router.message(Command("start"))
async def start_command(message: Message):
    await message.answer(
        "Привет! Выберите тему для викторины:",
        reply_markup=topic_keyboard()
    )


# Основная функция для запуска бота
async def main():
    logging.basicConfig(level=logging.INFO)  # Устанавливаем уровень логгирования

    # Инициализация бота и диспетчера
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Используем async_sessionmaker для создания сессий базы данных
    session_maker = async_sessionmaker

    # Подключаем наше Middleware для проверки доступа и передаем фабрику сессий
    dp.message.middleware(ChatAccessMiddleware(ALLOWED_USERS, async_sessionmaker))

    # Регистрация middleware для передачи сессии в хендлеры
    dp.message.middleware(DbSessionMiddleware(session_maker))
    dp.callback_query.middleware(DbSessionMiddleware(session_maker))

    # Регистрация роутеров
    dp.include_router(quiz_router)
    dp.include_router(group_publisher_router)
    dp.include_router(user_router)
    dp.include_router(start_router)

    try:
        # Запуск поллинга
        await dp.start_polling(bot)
    finally:
        # Закрываем сессию бота при завершении работы
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())