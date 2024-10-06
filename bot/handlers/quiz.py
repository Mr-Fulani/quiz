import asyncio
import io
import json
import os
import logging
import random

import aiogram
from PIL import Image
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.inline import topic_keyboard, get_confirmation_keyboard, get_publish_group_keyboard, \
    get_task_or_json_keyboard
from bot.keyboards.reply import main_menu_keyboard
from bot.services.image_service import generate_console_image, generate_image_name
from bot.services.s3_service import upload_to_s3
from bot.services.text_service import is_valid_url
from bot.services.message_service import send_message_with_retry, send_photo_with_retry  # Добавлено для обработки ожидания
from bot.states import QuizStates
from config import GROUP_CHAT_ID
from database.models import Task, Group
from datetime import datetime


quiz_router = Router()

# Создаем роутер
router = Router()

# Инициализация логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')



# Обработчик нажатия на кнопку "Создать задачу"
@router.message(F.text == "Создать задачу")
async def create_task(message: Message):
    await message.answer(
        "Выберите тему для задачи:",
        reply_markup=topic_keyboard()
    )




# Хэндлер для обработки выбора темы
@router.callback_query(F.data.startswith("topic_"))
async def choose_topic(callback_query: types.CallbackQuery, state: FSMContext):
    topic = callback_query.data.split("_")[1]
    await state.update_data(topic=topic)

    await callback_query.message.answer(
        f"Вы выбрали тему: {topic}. Введите подтему или введите '0' для пропуска."
    )
    await state.set_state(QuizStates.waiting_for_subtopic)

    # Удаление клавиатуры после нажатия кнопки
    await callback_query.answer()
    await callback_query.message.edit_reply_markup()



@quiz_router.message(QuizStates.waiting_for_subtopic)
async def process_subtopic(message: types.Message, state: FSMContext):
    """
    Обработчик ввода подтемы.

    Если подтемы нет, пользователь может ввести '0' для пропуска.
    """
    subtopic = message.text.strip()

    if subtopic.lower() == "0":
        subtopic = None
        await send_message_with_retry(
            bot=message.bot,
            chat_id=message.chat.id,
            text="Вы пропустили ввод подтемы."
        )
        logging.info("Подтема пропущена пользователем.")
    else:
        await send_message_with_retry(
            bot=message.bot,
            chat_id=message.chat.id,
            text=f"Подтема выбрана: {subtopic}"
        )
        logging.info(f"Подтема выбрана: {subtopic}")

    await state.update_data(subtopic=subtopic)

    # Запрос краткого описания задачи
    await send_message_with_retry(
        bot=message.bot,
        chat_id=message.chat.id,
        text="Введите краткое описание задачи или введите '0' для пропуска."
    )
    await state.set_state(QuizStates.waiting_for_short_description)




@quiz_router.message(QuizStates.waiting_for_short_description)
async def process_short_description(message: types.Message, state: FSMContext):
    """
    Обработчик ввода краткого описания задачи.

    Если описание пропущено, сохраняет значение None.
    """
    short_description = message.text.strip()

    if short_description == '0':
        short_description = None
        await send_message_with_retry(bot=message.bot,
        chat_id=message.chat.id,
        text="Описание пропущено.")
        logging.info("Пользователь пропустил ввод краткого описания.")
    else:
        await state.update_data(short_description=short_description)
        await send_message_with_retry(bot=message.bot,
        chat_id=message.chat.id,
        text="Описание добавлено.")
        logging.info(f"Краткое описание добавлено: {short_description}")

    # Переход к этапу ввода языка
    await send_message_with_retry(bot=message.bot,
        chat_id=message.chat.id,
        text="Введите язык задачи (например, 'ru' для русского, 'en' для английского).")
    await state.set_state(QuizStates.waiting_for_language)




@quiz_router.message(QuizStates.waiting_for_language)
async def process_language(message: types.Message, state: FSMContext):
    """
    Обработчик ввода языка задачи.

    Проверяет введенный язык и сохраняет его в состояние.
    """
    language = message.text.strip().lower()

    if language not in ['ru', 'en', 'es', 'tur']:
        await send_message_with_retry(bot=message.bot,
        chat_id=message.chat.id,
        text="Недопустимый язык. Введите 'ru', 'en', 'es', или 'tur'.")
        logging.warning(f"Неверный язык введен: {language}")
        return

    await state.update_data(language=language)
    logging.info(f"Язык задачи сохранен: {language}")
    await send_message_with_retry(bot=message.bot,
        chat_id=message.chat.id,
        text="Язык задачи сохранен. Введите текст задачи.")

    # Переход к этапу ввода вопроса
    await state.set_state(QuizStates.waiting_for_question)




@quiz_router.message(QuizStates.waiting_for_question)
async def process_question(message: types.Message, state: FSMContext):
    """
    Обработчик ввода текста задачи.

    Сохраняет текст задачи и генерирует изображение для предварительного просмотра.
    """
    task_text = message.text.strip()
    logging.info(f"Текст задачи: {task_text}")

    await state.update_data(question=task_text)

    logo_path = "assets/logo.png"
    image = generate_console_image(task_text, logo_path)
    logging.info("Изображение с задачей сгенерировано.")

    temp_file_path = "task_image.png"
    image.save(temp_file_path)

    try:
        await send_photo_with_retry(bot=message.bot,
            chat_id=message.chat.id,
            photo=types.FSInputFile(temp_file_path))
        logging.info("Изображение отправлено пользователю.")
        await send_message_with_retry(bot=message.bot,
        chat_id=message.chat.id,
        text="Изображение задачи успешно сгенерировано. Введите 4 варианта ответа через запятую.")
    except Exception as e:
        logging.error(f"Ошибка при отправке изображения: {e}")
        await send_message_with_retry(bot=message.bot,
        chat_id=message.chat.id,
        text=f"Ошибка при отправке изображения: {str(e)}")
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            logging.info("Временный файл изображения удалён.")

    # Переход к этапу ввода вариантов ответов
    await state.set_state(QuizStates.waiting_for_answers)




@quiz_router.message(QuizStates.waiting_for_answers)
async def process_answers(message: types.Message, state: FSMContext):
    """
    Обработчик ввода вариантов ответов.

    Проверяет количество введенных ответов и сохраняет их в состоянии.
    """
    answers = [a.strip() for a in message.text.split(',') if a.strip()]
    logging.info(f"Введенные варианты ответов: {answers}")

    if len(answers) != 4:
        await send_message_with_retry(bot=message.bot,
            chat_id=message.chat.id,
            text="Ошибка: Введите ровно 4 варианта ответа.")
        logging.warning("Неверное количество ответов введено пользователем.")
        return

    await state.update_data(answers=answers)
    await send_message_with_retry(bot=message.bot,
            chat_id=message.chat.id,
            text="Варианты ответа сохранены. Укажите правильный ответ.")
    await state.set_state(QuizStates.waiting_for_correct_answer)




@quiz_router.message(QuizStates.waiting_for_correct_answer)
async def process_correct_answer(message: types.Message, state: FSMContext):
    """
    Обработчик ввода правильного ответа.

    Проверяет наличие правильного ответа в списке вариантов и сохраняет его.
    """
    correct_answer = message.text.strip()
    data = await state.get_data()

    if correct_answer not in data['answers']:
        await send_message_with_retry(bot=message.bot,
            chat_id=message.chat.id,
            text="Ошибка: Правильный ответ должен быть одним из введенных вариантов.")
        logging.warning(f"Пользователь ввел некорректный правильный ответ: {correct_answer}")
        return

    await state.update_data(correct_answer=correct_answer)
    await send_message_with_retry(bot=message.bot,
            chat_id=message.chat.id,
            text="Правильный ответ сохранен. Введите краткое пояснение к задачке.")
    await state.set_state(QuizStates.waiting_for_explanation)




@quiz_router.message(QuizStates.waiting_for_explanation)
async def process_explanation(message: types.Message, state: FSMContext):
    """
    Обработчик ввода пояснения к задаче.

    Сохраняет пояснение и переходит к этапу ввода ссылки на ресурс.
    """
    explanation = message.text.strip()
    await state.update_data(explanation=explanation)
    logging.info(f"Пояснение к задаче: {explanation}")
    await send_message_with_retry(bot=message.bot,
            chat_id=message.chat.id,
            text="Пояснение сохранено. Введите ссылку на дополнительный ресурс.")
    await state.set_state(QuizStates.waiting_for_resource_link)






@quiz_router.message(QuizStates.waiting_for_resource_link)
async def process_resource_link(message: types.Message, state: FSMContext):
    """
    Обработчик ввода ссылки на ресурс.

    Запрашивает у пользователя ссылку на ресурс, проверяет ее корректность,
    генерирует изображение с вопросом и готовит задачу к запуску.
    """
    resource_link = message.text.strip()

    # Проверяем корректность ссылки
    if not is_valid_url(resource_link):
        await message.answer("Ошибка: Введите корректную ссылку.")
        return

    # Получаем данные из состояния
    data = await state.get_data()
    temp_file_path = "temp_task_image.png"

    # Генерируем изображение и сохраняем во временный файл
    image = generate_console_image(data['question'], "assets/logo.png")
    image.save(temp_file_path)
    await state.update_data(resource_link=resource_link, temp_image_path=temp_file_path)

    quiz_text = (
        f"Тема: {data['topic']}\n"
        f"Подтема: {data.get('subtopic', 'Без подтемы')}\n\n"
        f"Варианты ответов:\n\n"
        f"1. {data['answers'][0]}\n"
        f"2. {data['answers'][1]}\n"
        f"3. {data['answers'][2]}\n"
        f"4. {data['answers'][3]}\n"
        f"5. Я не знаю, но хочу узнать\n\n"
        f"Ссылка на ресурс: {resource_link}"
    )

    try:
        # Отправка изображения пользователю
        await message.answer_photo(photo=types.FSInputFile(temp_file_path), caption=quiz_text,
                                   reply_markup=get_confirmation_keyboard())
        logging.info("Изображение и текст отправлены с кнопками подтверждения.")

        await message.answer("Задача готова к подтверждению. Выберите, что делать: запустить или отменить.")

    except Exception as e:
        logging.error(f"Ошибка при отправке изображения: {e}")
        await message.answer(f"Ошибка при отправке изображения: {str(e)}")

    # Устанавливаем состояние FSM для следующего этапа
    await state.set_state(QuizStates.confirming_quiz)




@quiz_router.callback_query(lambda query: query.data == "confirm_launch")
async def confirm_quiz(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    logging.info(f"Полученные данные из состояния: {data}")

    # Получаем значение языка из состояния FSM
    language = data.get('language')  # Получаем язык из состояния

    if not language:
        logging.error("Язык не указан в данных состояния.")
        await callback.message.answer("Ошибка: язык задачи не найден.")
        return


    # Генерация имени для изображения
    image_name = generate_image_name(data['topic'])
    logging.info(f"Генерация имени изображения: {image_name}")


    try:
        # Загрузка изображения в S3
        image_url = upload_to_s3(Image.open(data['temp_image_path']), image_name)
        logging.info(f"Изображение успешно загружено в S3: {image_url}")
        await state.update_data(image_url=image_url)
    except Exception as e:
        logging.error(f"Ошибка при загрузке изображения в S3: {e}")
        await callback.message.answer("Ошибка при загрузке изображения.")
        return

    # Подготовка данных для сохранения
    correct_answer = data.get('correct_answer')
    answers = data.get('answers', [])
    wrong_answers = [answer for answer in answers if answer != correct_answer]

    logging.info(f"Правильный ответ: {correct_answer}")
    logging.info(f"Неправильные ответы: {wrong_answers}")

    short_description = data.get('short_description', '')
    logging.info(f"Краткое описание перед сохранением: {short_description}")

    # Проверка наличия всех необходимых данных
    if not all([data['topic'], correct_answer, wrong_answers, data['explanation'], image_url]):
        logging.error("Не все необходимые поля заполнены")
        await callback.message.answer("Ошибка: не все необходимые данные предоставлены")
        return

    logging.info(f"Краткое описание перед сохранением: {short_description}")

    # Сохранение задачи в базу данных
    try:
        async with session.begin():
            new_task = Task(
                topic=data['topic'],
                subtopic=data.get('subtopic', ''),
                question=data['question'],
                correct_answer=correct_answer,
                wrong_answers=wrong_answers,
                explanation=data['explanation'],
                resource_link=data['resource_link'],
                image_url=image_url,
                short_description=short_description,  # Сохраняем краткое описание
                language=language,  # Передаем язык задачи
                default_language=data.get('default_language', 'ru')
            )
            session.add(new_task)
            await session.flush()  # Чтобы получить ID новой задачи
            logging.info(f"Задача сохранена в базе данных: {new_task.id}")

            # Сохраняем ID задачи в состояние FSM
            await state.update_data(task_id=new_task.id)

        # Подтверждение сохранения
        await callback.message.answer(
            "Задача успешно сохранена с ID: {new_task.id}",
            reply_markup=get_publish_group_keyboard()
        )
        logging.info(f"Отправлено сообщение с клавиатурой для публикации задачи: get_publish_group_keyboard()")

    except Exception as e:
        logging.error(f"Ошибка при сохранении задачи в базе данных: {e}")
        await callback.message.answer(f"Ошибка при сохранении задачи в базе данных: {str(e)}")
        return

    # Отправляем задачу в чат с кнопками
    try:
        quiz_text = (
            f"Тема: {data['topic']}\n"
            f"Подтема: {data.get('subtopic', 'Без подтемы')}\n"
            f"Варианты ответов:\n"
            f"1. {data['answers'][0]}\n"
            f"2. {data['answers'][1]}\n"
            f"3. {data['answers'][2]}\n"
            f"4. {data['answers'][3]}\n"
            f"5. Я не знаю, но хочу узнать\n\n"
            f"Ссылка на ресурс: {data['resource_link']}"
        )

        await callback.message.answer_photo(photo=image_url, caption=quiz_text, reply_markup=get_publish_group_keyboard())
        logging.info("Задача готова к запуску. Предлагаем опубликовать или отменить.")
    except Exception as e:
        logging.error(f"Ошибка при отправке задачи в чат: {e}")
        await callback.message.answer(f"Ошибка при отправке задачи в чат: {str(e)}")




@quiz_router.callback_query(lambda query: query.data == "confirm_cancel")
async def cancel_quiz(callback: types.CallbackQuery, state: FSMContext):
    """
    Обработчик отмены викторины.
    """
    data = await state.get_data()

    # Удаление временного изображения
    if os.path.exists(data.get('temp_image_path', '')):
        os.remove(data['temp_image_path'])
        logging.info("Временный файл изображения удалён после отмены.")

    await callback.message.answer("Викторина отменена. Данные не были сохранены.")
    await callback.message.edit_reply_markup()
    await state.clear()





''' ??? '''
@quiz_router.callback_query(lambda query: query.data == "new_task")
async def start_new_quiz(callback: types.CallbackQuery, state: FSMContext):
    logging.info("Кнопка 'Новая задача' была нажата.")
    await callback.message.answer("Выберите тему для новой задачи:", reply_markup=topic_keyboard())
    await state.set_state(QuizStates.waiting_for_topic)






# @quiz_router.callback_query(lambda query: query.data == "upload_json")
# async def upload_tasks_via_json(callback: types.CallbackQuery, state: FSMContext):
#     """
#     Обработчик для загрузки задач из JSON файла.
#     """
#     await callback.message.answer("Пожалуйста, загрузите JSON файл с задачами.")
#     await state.set_state(QuizStates.waiting_for_file)
#     logging.info("Переход в состояние ожидания файла JSON.")



@router.message(F.text == "Загрузить JSON")
async def upload_tasks_via_json(message: Message, state: FSMContext):
    """
    Обработчик для загрузки задач из JSON файла.
    """
    await message.answer("Пожалуйста, загрузите JSON файл с задачами.")
    await state.set_state(QuizStates.waiting_for_file)  # Устанавливаем состояние ожидания файла
    logging.info("Переход в состояние ожидания файла JSON.")







@quiz_router.message(QuizStates.waiting_for_file, F.document)
async def process_tasks_file(message: types.Message, state: FSMContext, session: AsyncSession):
    try:
        # Получаем объект файла
        document = message.document
        file_info = await message.bot.get_file(document.file_id)
        logging.info(f"File info: {file_info.file_path}")

        # Загружаем файл в буфер
        file_buffer = io.BytesIO()
        await message.bot.download_file(file_info.file_path, destination=file_buffer)

        # Возвращаем курсор буфера в начало
        file_buffer.seek(0)

        # Читаем содержимое как JSON
        data = json.load(file_buffer)

        # Проверяем, что JSON содержит ключ 'tasks' и что это список
        if not isinstance(data, dict) or 'tasks' not in data or not isinstance(data['tasks'], list):
            await message.answer("Ошибка: Некорректная структура JSON-файла. Ожидался объект с ключом 'tasks', содержащий массив задач.")
            return

        tasks = data['tasks']
        logging.info(f"Загружено задач: {len(tasks)}")

        for task in tasks:
            # Генерация изображения для каждой задачи (используем язык по умолчанию)
            default_language = task.get('default_language', 'ru')
            question = task['question'].get(default_language, '')
            correct_answer = task['correct_answer'].get(default_language, '')
            wrong_answers = task['wrong_answers'].get(default_language, [])
            explanation = task['explanation'].get(default_language, '')
            short_description = task['short_description'].get(default_language, '')

            image = generate_console_image(question, "assets/logo.png")
            image_name = generate_image_name(task['topic'])
            image_url = upload_to_s3(image, image_name)

            # Сохраняем задачу в базу данных, храним `wrong_answers` как JSON-список
            new_task = Task(
                topic=task['topic'],
                subtopic=task.get('subtopic', ''),
                question=question,
                correct_answer=correct_answer,
                wrong_answers=wrong_answers,  # Сохраняем как JSON
                explanation=explanation,
                resource_link=task['resource_link'],
                image_url=image_url,
                short_description=short_description,
                default_language=default_language,
                language=task.get('language', default_language)
            )
            session.add(new_task)

        # Коммитим транзакцию
        await session.commit()
        logging.info(f"Все задачи сохранены в базу данных.")
        await message.answer(f"Загружено задач: {len(tasks)}")

        # Сохраняем ID последней задачи в состояние FSM
        await state.update_data(task_id=new_task.id)

    except json.JSONDecodeError:
        await message.answer("Ошибка: Неверный формат файла. Пожалуйста, загрузите корректный JSON-файл.")
    except Exception as e:
        logging.error(f"Ошибка при загрузке файла: {e}")
        await message.answer(f"Ошибка при загрузке файла: {e}")







@quiz_router.callback_query(lambda query: query.data == "confirm_launch")
async def confirm_launch(callback: types.CallbackQuery, state: FSMContext):
    # Логика запуска викторины
    await callback.message.answer("Викторина запущена!")

    # Замена кнопок на "Новая задача" и "JSON с задачками"
    await callback.message.edit_reply_markup(reply_markup=get_task_or_json_keyboard())
    await state.clear()






@quiz_router.callback_query(lambda query: query.data == "confirm_cancel")
async def confirm_cancel(callback: types.CallbackQuery, state: FSMContext):
    """
    Обработчик отмены задачи.
    """
    data = await state.get_data()

    # Удаление временного изображения
    if os.path.exists(data.get('temp_image_path', '')):
        os.remove(data['temp_image_path'])
        logging.info("Временный файл изображения удалён после отмены.")

    await callback.message.answer(
        "Викторина отменена. Данные не были сохранены.",
        reply_markup=main_menu_keyboard()  # Отображаем главное меню
    )
    await callback.message.edit_reply_markup()
    await state.clear()





@quiz_router.callback_query(lambda query: query.data == "publish_to_group")
async def publish_to_group(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    """
    Публикация задачи в группу.

    Отправляет изображение и викторину в указанную группу и обновляет запись в базе данных.
    """
    data = await state.get_data()
    logging.info(f"Данные из состояния: {data}")

    task_id = data.get('task_id')
    if not task_id:
        logging.error("Ошибка: ID задачи отсутствует.")
        await callback.message.answer("Ошибка: ID задачи отсутствует.")
        return

    try:
        # Извлекаем задачу из базы данных
        task = await session.get(Task, task_id)
        if not task:
            logging.error(f"Ошибка: задача с ID {task_id} не найдена.")
            await callback.message.answer(f"Ошибка: задача с ID {task_id} не найдена.")
            return

        # Получаем язык задачи, который был сохранен в момент создания
        language = task.language
        logging.info(f"Используем язык задачи для публикации: {language}")

        # Проверяем, есть ли группа для данной темы и языка
        group_query = select(Group).where(Group.topic == task.topic, Group.language == language)
        group = await session.execute(group_query)
        group_instance = group.scalar_one_or_none()

        if not group_instance:
            logging.warning(f"Группа для темы '{task.topic}' и языка '{language}' не найдена.")
            await callback.message.answer(
                f"Группа для темы '{task.topic}' и языка '{language}' не найдена.\n\n"
                "Задача сохранена, но публикация не выполнена. Как только будет создана соответствующая группа, вы сможете опубликовать задачу."
            )
            return


            # Если группа найдена, логируем подробности
        logging.info(f"Найдена группа: ID={group_instance.id}, Имя={group_instance.group_name},"
                f" Язык={group_instance.language}")

        group_chat_id = group_instance.group_id
        group_db_id = group_instance.id
        logging.info(f"ID группы для публикации (group_id): {group_chat_id}")
        logging.info(f"ID группы в базе данных (id): {group_db_id}")


        # Отправляем изображение в группу с кнопкой "Узнать подробнее"
        try:
            await callback.bot.send_photo(
                chat_id=group_chat_id,
                photo=task.image_url,
                caption=f"Тема: {task.topic}\nПодтема: {task.subtopic or 'Без подтемы'}",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="Узнать подробнее", url=task.resource_link)]
                ])
            )
            logging.info(f"Изображение отправлено в группу: {task.image_url}")
        except aiogram.exceptions.TelegramRetryAfter as e:
            logging.warning(f"Попадание в лимит Telegram: ждем {e.retry_after} секунд.")
            await asyncio.sleep(e.retry_after)
            return await publish_to_group(callback, state, session)  # Попробуем снова после ожидания
        except Exception as e:
            logging.error(f"Ошибка при отправке изображения в группу: {e}")
            await callback.message.answer(f"Ошибка при отправке изображения в группу: {e}")
            return

        # Перемешивание вариантов ответов
        options = task.wrong_answers + [task.correct_answer]
        random.shuffle(options)  # Перемешиваем список вариантов

        # Определяем индекс правильного ответа в перемешанном списке
        correct_option_id = options.index(task.correct_answer)

        # Отправляем опрос в группу
        try:
            await callback.bot.send_poll(
                chat_id=group_chat_id,
                question=task.question,
                options=options,
                type="quiz",
                correct_option_id=correct_option_id,
                explanation=task.explanation,
                is_anonymous=False
            )
            logging.info(f"Опрос отправлен в группу: {task.question}")

        except aiogram.exceptions.TelegramRetryAfter as e:
            logging.warning(f"Попадание в лимит Telegram: ждем {e.retry_after} секунд.")
            await asyncio.sleep(e.retry_after)
            return await publish_to_group(callback, state, session)  # Повтор после ожидания
        except Exception as e:
            logging.error(f"Ошибка при отправке опроса: {e}")
            await callback.message.answer(f"Ошибка при отправке опроса: {e}")
            return

        # Обновляем информацию о задаче в базе данных
        current_time = datetime.utcnow()
        logging.info(f"Обновление задачи: установка group_id = {group_db_id}")

        stmt = (
            update(Task)
            .where(Task.id == task_id)
            .values(
                published=True,
                publish_date=current_time,
                group_id=group_db_id  # Используем ID записи группы из таблицы groups
            )
        )
        await session.execute(stmt)
        await session.flush()
        await session.commit()

        logging.info(f"Задача с ID {task_id} успешно обновлена в базе данных и опубликована в группе.")
        await callback.message.answer("Задача успешно опубликована в группе.")

    except Exception as e:
        logging.error(f"Ошибка при публикации задачи: {e}")
        await callback.message.answer(f"Произошла ошибка при публикации задачи: {str(e)}")
        await session.rollback()
        logging.info("Выполнен откат изменений")

    finally:
        await state.clear()
        logging.info("Состояние очищено.")




async def publish_task_to_group(callback, task, group_chat_id, session):
    try:
        # Отправляем изображение в группу
        await callback.bot.send_photo(
            chat_id=group_chat_id,
            photo=task.image_url,
            caption=f"Тема: {task.topic}\nПодтема: {task.subtopic or 'Без подтемы'}"
        )
        logging.info(f"Изображение отправлено в группу: {task.image_url}")

        # Отправляем викторину
        options = task.wrong_answers + [task.correct_answer]  # Добавляем правильный ответ к неверным
        await callback.bot.send_poll(
            chat_id=group_chat_id,
            question=task.question,
            options=options,
            type="quiz",
            correct_option_id=options.index(task.correct_answer),
            explanation=task.explanation,
            is_anonymous=False
        )
        logging.info(f"Викторина отправлена: {task.question}")

        # Обновление информации о задаче в базе данных
        current_time = datetime.utcnow()
        stmt = (
            update(Task)
            .where(Task.id == task.id)
            .values(
                published=True,
                publish_date=current_time,
                group_id=group_chat_id
            )
        )
        await session.execute(stmt)
        await session.commit()
        logging.info(f"Задача с ID {task.id} успешно опубликована и обновлена в базе данных.")

        await callback.message.answer(f"Задача успешно опубликована в группе.")
    except Exception as e:
        logging.error(f"Ошибка при публикации задачи в группу: {e}")
        await callback.message.answer(f"Ошибка при публикации задачи в группу: {str(e)}")
