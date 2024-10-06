import asyncio
import logging
from datetime import datetime, timezone
import random
from zoneinfo import ZoneInfo

import aiogram
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database.models import Task, Group
from config import GROUP_CHAT_ID

from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from bot.states import QuizStates



router = Router()


# Создаем роутер
group_publisher_router = Router()


# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Пример лога для теста
logging.info("Запущена публикация задач в группы.")



''' проверка работы роутера '''
@group_publisher_router.message()
async def handle_all_messages(message: types.Message):
    logging.info(f"[group_quiz_handler] Получено сообщение: {message.text}")




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







async def get_group_for_task(session: AsyncSession, task: Task):
    """
    Получает группу из базы данных, соответствующую теме и языку задачи.
    """
    try:
        group_query = select(Group).where(Group.topic == task.topic, Group.language == task.language)
        group_result = await session.execute(group_query)
        group_instance = group_result.scalar_one_or_none()

        if group_instance:
            logging.info(f"Найдена группа для публикации: ID={group_instance.id}, Имя={group_instance.group_name}, Язык={group_instance.language}")
            return group_instance
        else:
            logging.warning(f"Группа для темы '{task.topic}' и языка '{task.language}' не найдена.")
            return None
    except Exception as e:
        logging.error(f"Ошибка при получении группы для задачи: {e}")
        return None





async def publish_task(message: types.Message, task: Task, session: AsyncSession):
    """
    Публикует одну задачу в соответствующую группу на основе языка и темы задачи.
    """

    # Словари для различных фраз на нескольких языках
    DONT_KNOW_OPTIONS = {
        'ru': "Я не знаю, но хочу узнать",
        'en': "I don't know, but I want to learn",
        'es': "No lo sé, pero quiero aprender",
        'tr': "Bilmiyorum, ama öğrenmek istiyorum"
    }

    LEARN_MORE_TEXT = {
        'ru': "Узнать подробнее",
        'en': "Learn more",
        'es': "Saber más",
        'tr': "Daha fazla öğren"
    }

    POLL_TEXT = {
        'ru': "Каким будет вывод?",
        'en': "What will be the output?",
        'es': "¿Cuál será el resultado?",
        'tr': "Çıktı ne olacak?"
    }

    try:
        # Получаем язык и тему задачи
        language = task.language
        topic = task.topic

        # Получаем внутренний ID группы из базы данных по языку и теме
        group_query = select(Group).where(Group.language == language, Group.topic == topic)
        group_instance = (await session.execute(group_query)).scalar_one_or_none()

        if not group_instance:
            await message.answer(
                f"Группа для темы '{task.topic}' и языка '{task.language}' не найдена. "
                "Задача сохранена, но публикация не выполнена."
            )
            logging.error(f"Группа для темы '{task.topic}' и языка '{task.language}' не найдена. Публикация отменена.")
            return

        group_chat_id = group_instance.group_id  # Реальный Telegram ID группы
        group_db_id = group_instance.id  # Внутренний ID группы в базе данных

        # Отправляем картинку с темой и подтемой
        intro_text = f"Тема: {task.topic}\nПодтема: {task.subtopic or 'Без подтемы'}"
        try:
            await message.bot.send_photo(chat_id=group_chat_id, photo=task.image_url, caption=intro_text)
            logging.info(f"Сообщение с картинкой отправлено в группу {group_chat_id}: {task.image_url}")
        except aiogram.exceptions.TelegramRetryAfter as e:
            logging.warning(f"Попадание в лимит Telegram: ждем {e.retry_after} секунд.")
            await asyncio.sleep(e.retry_after)
            return await publish_task(message, task, session)  # Повтор после ожидания
        except Exception as e:
            logging.error(f"Ошибка при отправке изображения в группу: {e}")
            await message.answer(f"Ошибка при отправке изображения в группу: {e}")
            return

        # Перемешиваем варианты ответов и добавляем вариант "Я не знаю, но хочу узнать" в конец
        wrong_answers = task.wrong_answers
        correct_answer = task.correct_answer
        options = wrong_answers + [correct_answer]

        random.shuffle(options)

        # Добавляем вариант "Я не знаю, но хочу узнать" на языке задачи
        dont_know_option = DONT_KNOW_OPTIONS.get(task.language, "Я не знаю, но хочу узнать")
        options.append(dont_know_option)
        correct_option_id = options.index(correct_answer)

        # Отправляем текст опроса
        poll_text = POLL_TEXT.get(task.language, "Каким будет вывод?")
        try:
            await message.bot.send_message(chat_id=group_chat_id, text=poll_text)
        except aiogram.exceptions.TelegramRetryAfter as e:
            logging.warning(f"Попадание в лимит Telegram: ждем {e.retry_after} секунд.")
            await asyncio.sleep(e.retry_after)
            return await publish_task(message, task, session)  # Повтор после ожидания
        except Exception as e:
            logging.error(f"Ошибка при отправке текста опроса: {e}")
            await message.answer(f"Ошибка при отправке текста опроса: {e}")
            return

        # Отправляем сам опрос
        try:
            await message.bot.send_poll(
                chat_id=group_chat_id,
                question=task.question,
                options=options,
                type="quiz",
                correct_option_id=correct_option_id,
                explanation=task.explanation,
                is_anonymous=False
            )
            logging.info(f"Опрос опубликован в группе {group_chat_id}: {task.question}")
        except aiogram.exceptions.TelegramRetryAfter as e:
            logging.warning(f"Попадание в лимит Telegram: ждем {e.retry_after} секунд.")
            await asyncio.sleep(e.retry_after)
            return await publish_task(message, task, session)  # Повтор после ожидания
        except Exception as e:
            logging.error(f"Ошибка при отправке опроса: {e}")
            await message.answer(f"Ошибка при отправке опроса: {e}")
            return

        # Отправляем кнопку "Узнать больше"
        learn_more_text = LEARN_MORE_TEXT.get(task.language, "Узнать больше")
        try:
            await message.bot.send_message(
                chat_id=group_chat_id,
                text="Узнать подробнее:",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                    [types.InlineKeyboardButton(text=learn_more_text, url=task.resource_link)]
                ])
            )
            logging.info(f"Кнопка 'Узнать больше' отправлена в группу {group_chat_id}.")
        except aiogram.exceptions.TelegramRetryAfter as e:
            logging.warning(f"Попадание в лимит Telegram: ждем {e.retry_after} секунд.")
            await asyncio.sleep(e.retry_after)
            return await publish_task(message, task, session)  # Повтор после ожидания
        except Exception as e:
            logging.error(f"Ошибка при отправке кнопки 'Узнать больше': {e}")
            await message.answer(f"Ошибка при отправке кнопки 'Узнать больше': {e}")
            return

        # Обновляем поля задачи в базе данных после успешной публикации
        success = await update_task_in_db(session, task, group_db_id)  # Используем внутренний ID группы
        if success:
            logging.info(f"Поля задачи с ID {task.id} успешно обновлены.")
        else:
            await message.answer(f"Ошибка при обновлении задачи с ID {task.id} в базе данных.")

    except Exception as e:
        logging.error(f"Ошибка при публикации задачи: {e}")




async def update_task_in_db(session: AsyncSession, task: Task, group_db_id):
    """
    Обновляет поля задачи в базе данных.
    """
    try:
        # Устанавливаем необходимые поля
        task.published = True
        task.publish_date = datetime.datetime.utcnow()  # Используем наивное время
        task.group_id = group_db_id  # Используем внутренний ID группы в базе данных

        # Добавляем объект `task` в сессию, чтобы убедиться, что он отслеживается
        session.add(task)

        # Коммитим изменения
        await session.commit()
        logging.info(f"Задача с ID {task.id} успешно обновлена в базе данных.")
        return True

    except Exception as e:
        logging.exception(f"Ошибка при обновлении задачи с ID {task.id}: {e}")
        await session.rollback()
        return False




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









@group_publisher_router.message(F.text == "Опубликовать по ID")
async def ask_for_task_id(message: types.Message, state: FSMContext):
    logging.info(f"Получено сообщение: {message.text}")
    logging.info(f"Состояние: {await state.get_state()}")
    logging.info("Обработчик 'Опубликовать по ID' вызван.")
    await message.answer("Пожалуйста, введите ID задачи для публикации:")
    await state.set_state(QuizStates.waiting_for_task_id)



@router.message(QuizStates.waiting_for_task_id)
async def publish_task_by_id(message: types.Message, state: FSMContext, session: AsyncSession):
    """
    Публикует конкретную задачу по введенному ID.
    """
    try:
        task_id = int(message.text.strip())  # Получаем ID задачи из сообщения
    except ValueError:
        await message.answer("Пожалуйста, укажите корректный ID задачи. Пример: 1")
        return

    # Получаем задачу из базы данных
    try:
        task = await fetch_task_by_id(session, task_id)
    except Exception as e:
        logging.exception(f"Ошибка при получении задачи с ID {task_id}: {e}")
        await message.answer(f"Ошибка при получении задачи с ID {task_id}.")
        return

    if not task:
        await message.answer(f"Задача с ID {task_id} не найдена.")
        return

    # Публикуем задачу
    try:
        await publish_task(message, task, session)
        await message.answer(f"Задача с ID {task_id} успешно опубликована.")
    except Exception as e:
        logging.exception(f"Ошибка при публикации задачи с ID {task_id}: {e}")
        await message.answer(f"Ошибка при публикации задачи с ID {task_id}.")
        return









# @group_publisher_router.message(Command("publish_task"))
# async def publish_task_by_id(message: types.Message, session: AsyncSession):
#     """
#     Публикует конкретную задачу по её ID.
#     """
#     try:
#         task_id = int(message.text.split()[1])  # Получаем ID задачи из сообщения
#     except (IndexError, ValueError):
#         await message.answer("Пожалуйста, укажите корректный ID задачи. Пример: /publish_task 1")
#         logging.warning("Некорректный ID задачи: %s", message.text)
#         return
#
#     # Получаем задачу из базы данных
#     try:
#         task = await fetch_task_by_id(session, task_id)
#     except Exception as e:
#         logging.exception(f"Ошибка при получении задачи с ID {task_id}: {e}")
#         await message.answer(f"Ошибка при получении задачи с ID {task_id}.")
#         return
#
#     if not task:
#         await message.answer(f"Задача с ID {task_id} не найдена.")
#         logging.info(f"Задача с ID {task_id} не найдена.")
#         return
#
#     # Публикуем задачу
#     try:
#         await publish_task(message, task, session)
#     except Exception as e:
#         logging.exception(f"Ошибка при публикации задачи с ID {task_id}: {e}")
#         await message.answer(f"Ошибка при публикации задачи с ID {task_id}.")
#         return

