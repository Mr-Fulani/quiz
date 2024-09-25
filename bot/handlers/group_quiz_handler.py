import asyncio
import logging
from aiogram import Router, types
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database.models import Task
from config import GROUP_CHAT_ID

# Создаем роутер
group_publisher_router = Router()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Пример лога для теста
logging.info("Запущена публикация задач в группы.")


async def fetch_tasks(session: AsyncSession):
    """
    Получает все задачи из базы данных.
    """
    async with session.begin():
        result = await session.execute(select(Task))
        tasks = result.scalars().all()
        logging.info(f"Найдено задач: {len(tasks)}")  # Лог для проверки количества задач
        return tasks



async def fetch_task_by_id(session: AsyncSession, task_id: int):
    """
    Получает задачу по ID.
    """
    async with session.begin():
        task = await session.get(Task, task_id)
        if not task:
            logging.warning(f"Задача с ID {task_id} не найдена.")
        return task



async def publish_task(message: types.Message, task: Task):
    """
    Публикует одну задачу в группу.
    """
    try:
        # Отправляем картинку с темой и подтемой
        intro_text = (
            f"Тема: {task.topic}\n"
            f"Подтема: {task.subtopic or 'Без подтемы'}"
        )
        await message.bot.send_photo(chat_id=GROUP_CHAT_ID, photo=task.image_url, caption=intro_text)
        logging.info(f"Сообщение с картинкой отправлено: {task.image_url}")

        # Проверяем и логируем правильные и неправильные ответы
        wrong_answers = task.wrong_answers
        if not isinstance(wrong_answers, list):
            logging.error(f"Ожидался список неправильных ответов, но получено: {type(wrong_answers)}")
            return

        correct_answer = task.correct_answer
        logging.info(f"Неверные ответы: {wrong_answers}")
        logging.info(f"Правильный ответ: {correct_answer}")

        # Добавляем вариант "Не знаю, но хочу узнать"
        options = wrong_answers + [correct_answer, "Я не знаю, но хочу узнать"]

        # Отправляем текст опроса
        poll_text = "Каким будет вывод?"
        await message.bot.send_message(chat_id=GROUP_CHAT_ID, text=poll_text)

        # Отправляем сам опрос
        await message.bot.send_poll(
            chat_id=GROUP_CHAT_ID,
            question=task.question,
            options=options,
            type="quiz",
            correct_option_id=options.index(correct_answer),  # Индекс правильного ответа
            explanation=task.explanation,
            is_anonymous=False
        )
        logging.info(f"Опрос опубликован: {task.question}")

        # Отправляем кнопку "Узнать больше"
        await message.bot.send_message(
            chat_id=GROUP_CHAT_ID,
            text="Узнать подробнее:",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="Узнать подробнее", url=task.resource_link)]
            ])
        )
        logging.info("Кнопка 'Узнать больше' отправлена.")
    except Exception as e:
        logging.error(f"Ошибка при публикации задачи: {e}")




@group_publisher_router.message(Command("publish_tasks"))
async def publish_tasks_in_group(message: types.Message, session: AsyncSession):
    tasks = await fetch_tasks(session)

    if not tasks:
        await message.answer("Нет задач для публикации.")
        logging.info("Нет задач для публикации.")
        return

    for i, task in enumerate(tasks):
        try:
            await publish_task(message, task)
            if (i + 1) % 2 == 0:
                await asyncio.sleep(20)  # Пауза 15 секунд после пары сообщений
            else:
                await asyncio.sleep(3)  # Пауза 1 секунда между сообщениями
        except Exception as e:
            if "Flood control exceeded" in str(e):
                retry_after = int(str(e).split("retry after ")[1].split()[0])
                logging.warning(f"Попадание в Flood control, пауза на {retry_after + 10} секунд...")
                await asyncio.sleep(retry_after + 10)
            else:
                logging.error(f"Неожиданная ошибка: {e}")
                break

    await message.answer("Все задачи успешно опубликованы.")
    logging.info("Все задачи успешно опубликованы.")




@group_publisher_router.message(Command("publish_task"))
async def publish_task_by_id(message: types.Message, session: AsyncSession):
    """
    Публикует конкретную задачу по её ID.
    """
    try:
        task_id = int(message.text.split()[1])  # Получаем ID задачи из сообщения
    except (IndexError, ValueError):
        await message.answer("Пожалуйста, укажите корректный ID задачи. Пример: /publish_task 1")
        return

    task = await fetch_task_by_id(session, task_id)

    if not task:
        await message.answer(f"Задача с ID {task_id} не найдена.")
        logging.info(f"Задача с ID {task_id} не найдена.")
        return

    await publish_task(message, task)
    await message.answer(f"Задача с ID {task_id} успешно опубликована.")
    logging.info(f"Задача с ID {task_id} успешно опубликована.")