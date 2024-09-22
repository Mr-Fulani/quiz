from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
from database.database import get_async_session
from database.models import Task
from aiogram import Bot


# Инициализация планировщика
scheduler = AsyncIOScheduler()


def schedule_task_post(task_id: int, post_time: datetime, bot: Bot):
    """
    Функция для планирования задачи на отложенный постинг.
    :param task_id: ID задачи для публикации
    :param post_time: Время публикации (формат datetime)
    :param bot: Экземпляр бота для отправки сообщений
    """
    scheduler.add_job(post_task_to_channel, 'date', run_date=post_time, args=[task_id, bot])


async def post_task_to_channel(task_id: int, bot: Bot):
    """
    Функция для публикации задачи в канал Telegram в отложенное время.
    :param task_id: ID задачи, которая будет опубликована
    :param bot: Экземпляр бота для отправки сообщений
    """
    async for session in get_async_session():
        task = await session.get(Task, task_id)
        if task:
            # Публикуем задачу в Telegram-канале
            await bot.send_message(
                chat_id="@your_channel",  # Замените на ваш канал
                text=f"Новая задача по теме: {task.topic}\n\n{task.question}\n\n"
                     f"Ответы: {task.wrong_answers}\n\nУзнать больше: {task.resource_link}",
                disable_web_page_preview=False
            )

# Запускаем планировщик
scheduler.start()
