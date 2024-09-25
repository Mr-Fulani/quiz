import asyncio
import os
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from alembic import context, op
from database.models import Base  # Импортируй модели
from dotenv import load_dotenv
import logging
import sqlalchemy as sa

# Загрузка конфигурации логов Alembic
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Настройка логирования
logger = logging.getLogger('alembic.runtime.migration')

# Задаём метаданные из моделей для Alembic
target_metadata = Base.metadata

# Загрузка переменных окружения
load_dotenv()

# URL подключения к базе данных
DATABASE_URL = os.getenv("DATABASE_URL")

# Создание асинхронного движка
def get_engine() -> AsyncEngine:
    logger.info("Создание асинхронного движка...")
    return create_async_engine(DATABASE_URL, poolclass=pool.NullPool)

# Асинхронная миграция
async def run_migrations_async():
    logger.info("Запуск асинхронной миграции...")
    connectable = get_engine()

    async with connectable.connect() as connection:
        logger.info("Установлено соединение с базой данных.")
        await connection.run_sync(do_run_migrations)

# Синхронная миграция для поддержки Alembic
def run_migrations():
    logger.info("Запуск синхронной миграции...")
    connectable = get_engine().sync_engine  # Преобразование в синхронный движок

    with connectable.connect() as connection:
        logger.info("Установлено соединение с базой данных (синхронный режим).")
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            logger.info("Выполнение миграций...")
            context.run_migrations()

def do_run_migrations(connection):
    logger.info("Конфигурация и запуск миграций...")
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        logger.info("Начало транзакции миграции...")
        context.run_migrations()
        logger.info("Миграции успешно выполнены.")

# Выполняем миграцию
if context.is_offline_mode():
    logger.info("Запуск миграции в оффлайн-режиме...")
    run_migrations()
else:
    logger.info("Запуск миграции в онлайн-режиме...")
    asyncio.run(run_migrations_async())







def upgrade():
    # Применяем изменение типа для колонки wrong_answers
    op.execute("ALTER TABLE tasks ALTER COLUMN wrong_answers TYPE JSON USING wrong_answers::json")


def downgrade():
    # Откат миграции (если потребуется вернуться обратно на строку)
    op.alter_column('tasks', 'wrong_answers', type_=sa.Text)




