import asyncio
import logging
from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import Message
from bot.handlers.group_quiz_handler import group_publisher_router
from bot.handlers.quiz import quiz_router, router
from bot.handlers.user_handler import user_router
from bot.middlewares.db_middleware import DbSessionMiddleware
from bot.middlewares.access_middleware import ChatAccessMiddleware
from bot.middlewares.user_update_middleware import UserUpdateMiddleware
from config import BOT_TOKEN, ALLOWED_USERS
from database.database import async_sessionmaker
from keyboards.reply import main_menu_keyboard  # Импорт функции для создания главного меню



# Создание нового роутера для команды /start
start_router = Router()









# Основная функция для запуска бота
async def main():
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Используем async_sessionmaker для создания сессий базы данных
    session_maker = async_sessionmaker

    # Подключаем middleware (важен порядок)
    dp.message.middleware(DbSessionMiddleware(session_maker))  # Должно идти перед UserUpdateMiddleware
    dp.message.middleware(UserUpdateMiddleware())
    dp.message.middleware(ChatAccessMiddleware(ALLOWED_USERS, async_sessionmaker))

    dp.callback_query.middleware(DbSessionMiddleware(session_maker))  # Подключаем для callback запросов
    dp.callback_query.middleware(UserUpdateMiddleware())



    # Регистрация роутеров
    logging.info("Регистрация роутеров")
    dp.include_router(router)
    logging.info("Роутер 'router' зарегистрирован")
    dp.include_router(group_publisher_router)
    logging.info("Роутер 'group_publisher_router' зарегистрирован")
    dp.include_router(user_router)
    logging.info("Роутер 'user_router' зарегистрирован")
    dp.include_router(start_router)
    logging.info("Роутер 'start_router' зарегистрирован")

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())