import logging
import os
import datetime

from aiogram.types import message
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from database.base import Base
from aiogram import Bot
from aiogram.types import User as TelegramUser
from sqlalchemy.future import select
from database.models import User



# Загружаем переменные окружения
load_dotenv()


# Подключение к базе данных через переменную окружения
DATABASE_URL = os.getenv("DATABASE_URL")


# Создаём движок для асинхронной работы с PostgreSQL
engine = create_async_engine(DATABASE_URL, echo=True)


# Создаём фабрику асинхронных сессий
async_sessionmaker = async_sessionmaker(bind=engine, expire_on_commit=False)


async def init_db() -> None:
    """
    Инициализация базы данных: создание таблиц.
    """
    async with engine.begin() as conn:
        # Синхронное создание всех таблиц на основе моделей
        await conn.run_sync(Base.metadata.create_all)



async def add_user_if_not_exists(user: TelegramUser, session: AsyncSession):
    logging.info(f"Вызов add_user_if_not_exists: ID={user.id}, Username={user.username}, Language={user.language_code}")

    try:
        query = select(User).where(User.telegram_id == user.id)
        result = await session.execute(query)
        existing_user = result.scalar_one_or_none()

        if existing_user:
            logging.info(f"Существующий пользователь найден: ID={user.id}, текущий язык={existing_user.language}")

            # Всегда обновляем язык, даже если он кажется тем же самым
            existing_user.language = user.language_code
            logging.info(f"Обновление языка пользователя: {existing_user.language} -> {user.language_code}")

            if existing_user.username != user.username:
                existing_user.username = user.username
                logging.info(f"Обновление имени пользователя: {existing_user.username} -> {user.username}")

            try:
                await session.commit()
                logging.info(f"Пользователь {user.id} обновлен в базе данных.")
            except Exception as e:
                logging.error(f"Ошибка при фиксации изменений в базе данных для пользователя {user.id}: {e}")
                await session.rollback()
        else:
            new_user = User(
                telegram_id=user.id,
                username=user.username,
                subscription_status='active',
                language=user.language_code,
                created_at=datetime.datetime.utcnow()
            )
            session.add(new_user)
            try:
                await session.commit()
                logging.info(f"Новый пользователь {user.id} добавлен в базу данных.")
            except Exception as e:
                logging.error(f"Ошибка при добавлении нового пользователя {user.id} в базе данных: {e}")
                await session.rollback()

    except Exception as e:
        logging.error(f"Ошибка при проверке или добавлении пользователя {user.id}: {e}")
        await session.rollback()

    logging.info(f"Завершение add_user_if_not_exists для пользователя {user.id}")