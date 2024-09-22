import asyncio

from aiogram import Bot, Dispatcher
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.handlers.quiz import quiz_router
from bot.keyboards.inline import topic_keyboard
from bot.middlewares.db_middleware import DbSessionMiddleware
from config import BOT_TOKEN

# Инициализация бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# Регистрация middleware для передачи сессии
dp.update.middleware(DbSessionMiddleware())

# Регистрация роутеров
dp.include_router(quiz_router)

# Создание нового роутера для команды /start
start_router = Router()


@start_router.message(Command("start"))
async def start_command(message: Message):
    await message.answer(
        "Привет! Выберите тему для викторины:",
        reply_markup=topic_keyboard()
    )

# Добавляем роутер команды /start в диспетчер
dp.include_router(start_router)


# Основная функция для запуска поллинга
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())