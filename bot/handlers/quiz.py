import os
import io
import json
import logging
from datetime import datetime

from PIL import Image
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import InputFile, BufferedInputFile, FSInputFile
from aiogram.fsm.context import FSMContext

from bot.keyboards.inline import get_confirmation_keyboard, get_task_or_json_keyboard, topic_keyboard
from bot.services.image_service import generate_console_image, generate_image_name
from sqlalchemy.ext.asyncio import AsyncSession
from bot.services.s3_service import upload_to_s3
from bot.services.scheduler_service import schedule_task_post
from bot.services.text_service import escape_markdown_v2, is_valid_url
from bot.states import QuizStates
from database.database import get_async_session
from database.models import Task
from aiogram import F

# Инициализация логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

quiz_router = Router()


# Обработчик выбора темы
@quiz_router.callback_query(lambda query: query.data.startswith("topic_"))
async def choose_topic(callback: types.CallbackQuery, state: FSMContext):
    topic = callback.data.split("_")[1]  # Извлекаем тему
    logging.info(f"Тема выбрана: {topic}")
    await state.update_data(topic=topic)  # Сохраняем тему в состояние
    await callback.message.answer("Введите текст задачки (например, отрывок кода).")
    await state.set_state(QuizStates.waiting_for_question)
    logging.info("Переход к состоянию: waiting_for_question")


# Обработчик ввода вопроса
@quiz_router.message(QuizStates.waiting_for_question)
async def process_question(message: types.Message, state: FSMContext):
    task_text = message.text.strip()  # Получаем текст задачки
    logging.info(f"Текст задачки: {task_text}")

    # Сохраняем текст задачи в состояние
    await state.update_data(question=task_text)

    logo_path = "assets/logo.png"  # Путь к логотипу

    # Генерируем изображение с задачкой и логотипом
    image = generate_console_image(task_text, logo_path)
    logging.info("Изображение с задачей сгенерировано.")

    # Сохраняем изображение во временный файл
    temp_file_path = "task_image.png"
    image.save(temp_file_path)

    try:
        # Отправляем файл пользователю
        await message.answer_photo(FSInputFile(temp_file_path))
        logging.info("Изображение отправлено пользователю.")
    except Exception as e:
        logging.error(f"Ошибка при отправке изображения: {e}")
    finally:
        # Удаляем временный файл после отправки
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            logging.info("Временный файл удалён.")

    # Переход к следующему шагу
    await message.answer("Введите 4 варианта ответа через запятую.")
    await state.set_state(QuizStates.waiting_for_answers)
    logging.info("Переход к состоянию: waiting_for_answers")


# Обработчик ввода вариантов ответов
@quiz_router.message(QuizStates.waiting_for_answers)
async def process_answers(message: types.Message, state: FSMContext):
    answers = [a.strip() for a in message.text.split(',')]
    logging.info(f"Введённые варианты ответа: {answers}")

    if len(answers) != 4:
        await message.answer("Пожалуйста, введите ровно 4 варианта ответа.")
        logging.warning("Пользователь ввёл не 4 варианта ответа.")
        return

    # Добавляем пятый вариант
    answers.append("Я не знаю, но хочу узнать")
    logging.info("Добавлен пятый вариант ответа: 'Я не знаю, но хочу узнать'.")

    await state.update_data(answers=answers)
    await message.answer("Укажите правильный ответ:")
    await state.set_state(QuizStates.waiting_for_correct_answer)
    logging.info("Переход к состоянию: waiting_for_correct_answer")





# Обработчик ввода правильного ответа
@quiz_router.message(QuizStates.waiting_for_correct_answer)
async def process_correct_answer(message: types.Message, state: FSMContext):
    correct_answer = message.text.strip()
    logging.info(f"Получен правильный ответ: {correct_answer}")

    # Получаем варианты ответов
    data = await state.get_data()
    logging.info(f"Существующие варианты ответов: {data['answers']}")

    if correct_answer not in data['answers']:
        logging.warning(f"Правильный ответ '{correct_answer}' не найден среди вариантов ответа")
        await message.answer("Правильный ответ должен быть одним из введённых вариантов.")
        return

    await state.update_data(correct_answer=correct_answer)
    logging.info(f"Правильный ответ '{correct_answer}' сохранён.")

    await message.answer("Введите краткое пояснение к задачке:")
    await state.set_state(QuizStates.waiting_for_explanation)
    logging.info("Переход к состоянию: waiting_for_explanation")


# Обработчик ввода пояснения
@quiz_router.message(QuizStates.waiting_for_explanation)
async def process_explanation(message: types.Message, state: FSMContext):
    explanation = message.text.strip()
    logging.info(f"Получено пояснение: {explanation}")

    await state.update_data(explanation=explanation)
    await message.answer("Введите ссылку на дополнительный ресурс:")
    await state.set_state(QuizStates.waiting_for_resource_link)
    logging.info("Переход к состоянию: waiting_for_resource_link")






@quiz_router.message(QuizStates.waiting_for_resource_link)
async def process_resource_link(message: types.Message, state: FSMContext):
    resource_link = message.text.strip()

    # Получаем данные из состояния
    data = await state.get_data()

    # Генерируем имя для временного файла изображения
    temp_file_path = "temp_task_image.png"

    # Генерируем изображение с задачей и логотипом
    image = generate_console_image(data['question'], "assets/logo.png")
    image.save(temp_file_path)  # Сохраняем изображение локально

    # Сохраняем ссылку на ресурс в состоянии
    await state.update_data(resource_link=resource_link, temp_image_path=temp_file_path)
    logging.info(f"Ссылка на ресурс сохранена: {resource_link}")

    # Отправляем изображение с кнопками подтверждения
    try:
        quiz_text = (
            f"Тема: {data['topic']}\n\n"
            f"Вопрос: {data['question']}\n\n"
            f"Варианты ответов:\n"
            f"1. {data['answers'][0]}\n"
            f"2. {data['answers'][1]}\n"
            f"3. {data['answers'][2]}\n"
            f"4. {data['answers'][3]}\n"
            f"5. Я не знаю, но хочу узнать\n\n"
            f"Ссылка на ресурс: {resource_link}"
        )

        await message.answer_photo(photo=FSInputFile(temp_file_path), caption=quiz_text,
                                   reply_markup=get_confirmation_keyboard())
        logging.info("Изображение отправлено пользователю с кнопками подтверждения.")
    except Exception as e:
        logging.error(f"Ошибка при отправке изображения: {e}")

    # Устанавливаем состояние подтверждения
    await state.set_state(QuizStates.confirming_quiz)










# Обработчик подтверждения запуска викторины
@quiz_router.callback_query(lambda query: query.data == "confirm_launch")
async def create_quiz(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    # Получаем данные из состояния
    data = await state.get_data()

    # Генерируем имя для изображения в S3
    image_name = generate_image_name(data['topic'])

    # Загружаем изображение в S3
    try:
        image_url = upload_to_s3(Image.open(data['temp_image_path']), image_name)
        logging.info(f"Изображение успешно загружено в S3: {image_url}")
    except Exception as e:
        logging.error(f"Ошибка при загрузке изображения в S3: {e}")
        await callback.message.answer("Ошибка при загрузке изображения. Попробуйте снова.")
        return

    # Сохранение задачи в базе данных
    try:
        new_task = Task(
            topic=data['topic'],
            question=data['question'],
            correct_answer=data['correct_answer'],
            wrong_answers=",".join([a for a in data['answers'] if a != data['correct_answer']]),
            explanation=data['explanation'],
            resource_link=data['resource_link'],
            image_url=image_url  # Сохраняем URL изображения
        )
        session.add(new_task)
        await session.commit()
        logging.info(f"Задача сохранена в базе данных: {new_task.id}")

        # Сначала отправляем изображение с текстом викторины
        quiz_text = (
            f"Тема: {data['topic']}\n\n"
            f"Вопрос: {data['question']}\n\n"
            f"Ссылка на ресурс: {data['resource_link']}"
        )

        await callback.message.answer_photo(photo=image_url, caption=quiz_text)
        logging.info("Изображение и текст викторины отправлены.")

        # Затем отправляем саму викторину
        await callback.message.answer_poll(
            question=data['question'],
            options=[
                data['answers'][0],
                data['answers'][1],
                data['answers'][2],
                data['answers'][3],
                "Я не знаю, но хочу узнать"
            ],
            type="quiz",
            correct_option_id=data['answers'].index(data['correct_answer']),
            explanation=data['explanation'],
            is_anonymous=False
        )
        logging.info("Викторина отправлена пользователю.")

    except Exception as e:
        logging.error(f"Ошибка при сохранении задачи в базе данных: {e}")

    # Удаляем временный файл изображения
    if os.path.exists(data['temp_image_path']):
        os.remove(data['temp_image_path'])
        logging.info("Временный файл изображения удалён.")

    # Заменяем кнопки на "Новая задача" и "JSON с задачами"
    await callback.message.edit_reply_markup(reply_markup=get_task_or_json_keyboard())
    await state.clear()







# Обработчик отмены викторины
@quiz_router.callback_query(lambda query: query.data == "confirm_cancel")
async def cancel_quiz(callback: types.CallbackQuery, state: FSMContext):
    # Получаем данные из состояния
    data = await state.get_data()

    # Удаляем временный файл изображения, если он существует
    if os.path.exists(data.get('temp_image_path', '')):
        os.remove(data['temp_image_path'])
        logging.info("Временный файл изображения удалён после отмены.")

    # Сообщаем пользователю об отмене
    await callback.message.answer("Викторина отменена. Данные не были сохранены.")

    # Заменяем кнопки на "Новая задача" и "JSON с задачами"
    await callback.message.edit_reply_markup(reply_markup=get_task_or_json_keyboard())
    await state.clear()





@quiz_router.callback_query(lambda query: query.data == "new_task")
async def start_new_quiz(callback: types.CallbackQuery, state: FSMContext):
    # Отправляем инлайн-клавиатуру с выбором темы для новой задачи
    try:
        await callback.message.answer("Выберите тему для новой задачи:",
                                      reply_markup=topic_keyboard())
        logging.info("Показаны кнопки выбора темы.")
    except Exception as e:
        logging.error(f"Ошибка при показе кнопок выбора темы: {e}")

    # Устанавливаем состояние ожидания выбора темы
    await state.set_state(QuizStates.waiting_for_topic)





@quiz_router.callback_query(lambda query: query.data == "upload_json")
async def upload_tasks_via_json(callback: types.CallbackQuery, state: FSMContext):
    # Начинаем процесс загрузки задач из JSON файла
    await callback.message.answer("Пожалуйста, загрузите JSON файл с задачами.")
    await state.set_state(QuizStates.waiting_for_file)
