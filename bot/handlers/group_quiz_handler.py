import os
import logging
from PIL import Image
from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from bot.services.image_service import generate_console_image, generate_image_name
from bot.services.s3_service import upload_to_s3
from config import GROUP_CHAT_ID
from database.models import Task
from sqlalchemy.ext.asyncio import AsyncSession
from bot.keyboards.inline import get_task_or_json_keyboard

group_quiz_router = Router()





@group_quiz_router.callback_query(lambda query: query.data == "confirm_launch_group")
async def create_quiz_for_group(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    """
    Обработчик подтверждения создания викторины для группы.
    Отправляет сообщение с картинкой, темой, подтемой и отдельно опросом.
    """
    data = await state.get_data()

    # Генерируем имя для изображения в S3
    image_name = generate_image_name(data['topic'], data.get('subtopic', ''))

    # Загружаем изображение в S3
    try:
        image_url = upload_to_s3(Image.open(data['temp_image_path']), image_name)
        logging.info(f"Изображение успешно загружено в S3: {image_url}")
    except Exception as e:
        logging.error(f"Ошибка при загрузке изображения в S3: {e}")
        await callback.message.answer("Ошибка при загрузке изображения.")
        return

    # Текст для первого сообщения: тема, подтема
    quiz_intro_text = (
        f"Тема: {data['topic']}\n"
        f"Подтема: {data.get('subtopic', 'Без подтемы')}"
    )

    # Отправляем первое сообщение с картинкой
    try:
        await callback.bot.send_photo(GROUP_CHAT_ID, photo=image_url, caption=quiz_intro_text)
        logging.info("Первое сообщение с картинкой отправлено в группу.")
    except Exception as e:
        logging.error(f"Ошибка при отправке картинки: {e}")

    # Текст для опроса
    poll_text = "Каким будет вывод?"

    # Отправляем опрос
    try:
        await callback.bot.send_message(chat_id=GROUP_CHAT_ID, text=poll_text)
        await callback.bot.send_poll(
            chat_id=GROUP_CHAT_ID,
            question=data['question'],
            options=data['answers'],
            type="quiz",
            correct_option_id=data['answers'].index(data['correct_answer']),
            explanation=data['explanation'],
            is_anonymous=False
        )
        logging.info("Опрос отправлен в группу.")
    except Exception as e:
        logging.error(f"Ошибка при отправке опроса: {e}")

    # Добавляем кнопку "Узнать больше"
    try:
        await callback.bot.send_message(
            chat_id=GROUP_CHAT_ID,
            text="Узнать подробнее:",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="Узнать подробнее", url=data['resource_link'])]
            ])
        )
        logging.info("Кнопка 'Узнать больше' отправлена.")
    except Exception as e:
        logging.error(f"Ошибка при отправке кнопки 'Узнать больше': {e}")

    # Сохраняем задачу в базу данных
    try:
        new_task = Task(
            topic=data['topic'],
            subtopic=data.get('subtopic', ''),
            question=data['question'],
            correct_answer=data['correct_answer'],
            wrong_answers=",".join([a for a in data['answers'] if a != data['correct_answer']]),
            explanation=data['explanation'],
            resource_link=data['resource_link'],
            image_url=image_url,
            short_description=data.get('short_description')  # Теперь это поле необязательное
        )
        session.add(new_task)
        await session.commit()
        logging.info(f"Задача сохранена в базе данных: {new_task.id}")
    except Exception as e:
        logging.error(f"Ошибка при сохранении задачи в базе данных: {e}")

    # Удаляем временный файл изображения
    if os.path.exists(data['temp_image_path']):
        os.remove(data['temp_image_path'])
        logging.info("Временный файл изображения удалён.")

    # Очищаем состояние
    await callback.message.edit_reply_markup(reply_markup=get_task_or_json_keyboard())
    await state.clear()

