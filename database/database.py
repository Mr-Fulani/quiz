import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from database.models import Base  # Импортируем модель базы данных


# Загружаем переменные окружения
load_dotenv()

# Подключение к базе данных через переменную окружения
DATABASE_URL = os.getenv("DATABASE_URL")

# Создаём движок для асинхронной работы с PostgreSQL
engine = create_async_engine(DATABASE_URL, echo=True)

# Создаём фабрику сессий
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db() -> None:
    """
    Инициализация базы данных: создание таблиц.
    """
    async with engine.begin() as conn:
        # Синхронное создание всех таблиц на основе моделей
        await conn.run_sync(Base.metadata.create_all)


# Функция для получения асинхронной сессии
async def get_async_session() -> AsyncSession:
    """
    Возвращает асинхронную сессию для взаимодействия с базой данных.
    Используется в других частях программы.
    """
    async with async_session() as session:
        yield session
