import logging
import os
import datetime

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from database.base import Base
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




# Функция для добавления пользователя, если его нет в базе
async def add_user_if_not_exists(user_data, session: AsyncSession):
    user_id = user_data.id
    username = user_data.username
    language_code = user_data.language_code  # Получаем язык пользователя из данных Telegram

    logging.info(f"Проверка пользователя: ID={user_id}, Username={username}, Language={language_code}")

    try:
        # Используем запрос для проверки наличия пользователя
        query = select(User).where(User.telegram_id == user_id)
        result = await session.execute(query)
        existing_user = result.scalar_one_or_none()

        if existing_user:
            # Проверка необходимости обновления данных
            needs_update = False

            # Проверка и обновление имени пользователя
            if existing_user.username != username:
                logging.info(f"Обновление имени пользователя: {existing_user.username} -> {username}")
                existing_user.username = username
                needs_update = True

            # Проверка и обновление языка пользователя
            if existing_user.language != language_code:
                logging.info(f"Обновление языка пользователя: {existing_user.language} -> {language_code}")
                existing_user.language = language_code
                needs_update = True

            # Если были изменения, фиксируем их в базе данных
            if needs_update:
                try:
                    await session.commit()
                    logging.info(f"Пользователь {user_id} обновлен в базе данных: Username={username}, Language={language_code}.")
                except Exception as e:
                    logging.error(f"Ошибка при фиксации изменений в базе данных для пользователя {user_id}: {e}")
                    await session.rollback()
            else:
                logging.info(f"Пользователь {user_id} уже существует в базе данных и данные актуальны.")
            return  # Завершаем выполнение функции, если пользователь существует

        # Если пользователь не найден, добавляем его в базу данных
        new_user = User(
            telegram_id=user_id,
            username=username,
            subscription_status='active',
            language=language_code,
            created_at=datetime.datetime.now(datetime.timezone.utc)  # Сохраняем дату и время создания пользователя
        )

        session.add(new_user)
        try:
            await session.commit()
            logging.info(f"Пользователь {user_id} добавлен в базу данных с данными: Username={username}, Language={language_code}.")
        except Exception as e:
            logging.error(f"Ошибка при добавлении нового пользователя {user_id} в базу данных: {e}")
            await session.rollback()

    except Exception as e:
        logging.error(f"Ошибка при проверке или добавлении пользователя {user_id}: {e}")
        await session.rollback()

    except Exception as e:
        logging.error(f"Ошибка при проверке или добавлении пользователя {user_id}: {e}")
        await session.rollback()