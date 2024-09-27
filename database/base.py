from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from config import DATABASE_URL



# Создаем базу данных моделей
Base = declarative_base()



# Создаем асинхронный движок для подключения к базе данных
async_engine = create_async_engine(DATABASE_URL, echo=True)



# Создаем фабрику асинхронных сессий
async_sessionmaker = sessionmaker(
    async_engine,
    expire_on_commit=False,
    class_=AsyncSession
)




