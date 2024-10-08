import io
import json
import os
import logging


from PIL import Image
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.services.image_service import generate_console_image, generate_image_name
from bot.services.s3_service import upload_to_s3
from bot.services.text_service import is_valid_url
from bot.keyboards.inline import get_confirmation_keyboard, get_task_or_json_keyboard, topic_keyboard, \
    main_menu_keyboard
from bot.states import QuizStates
from database.models import Task






quiz_router = Router()


# Инициализация логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


@quiz_router.callback_query(lambda query: query.data.startswith("topic_"))
async def choose_topic(callback: types.CallbackQuery, state: FSMContext):
    """
    Обработчик выбора темы викторины.
    """
    topic = callback.data.split("_")[1]
    logging.info(f"Тема выбрана: {topic}")

    # Сохраняем тему в состояние
    await state.update_data(topic=topic)

    # Отправляем сообщение с предложением ввести подтему или "0" для пропуска
    await callback.message.answer(
        f"Вы выбрали тему: {topic}. Введите подтему (например, 'Списки') или введите '0' для пропуска.")

    # Устанавливаем состояние ожидания подтемы
    await state.set_state(QuizStates.waiting_for_subtopic)


@quiz_router.message(QuizStates.waiting_for_subtopic)
async def process_subtopic(message: types.Message, state: FSMContext):
    """
    Обработчик ввода подтемы. Если подтемы нет, можно ввести '0'.
    """
    subtopic = message.text.strip()

    # Если пользователь ввел '0', пропускаем подтему
    if subtopic.lower() == "0":
        subtopic = None  # Очищаем подтему
        await message.answer("Вы пропустили ввод подтемы.")
    else:
        await message.answer(f"Подтема выбрана: {subtopic}")

    # Сохраняем подтему в состояние
    await state.update_data(subtopic=subtopic)

    # Переход к следующему этапу: ввод краткого описания
    await message.answer("Введите краткое описание задачи или введите '0' для пропуска.")
    await state.set_state(QuizStates.waiting_for_short_description)





@quiz_router.message(QuizStates.waiting_for_short_description)
async def process_short_description(message: types.Message, state: FSMContext):
    """
    Обработчик ввода краткого описания задачи. Поле необязательно, можно пропустить.
    """
    short_description = message.text.strip()

    # Если пользователь решил пропустить описание
    if short_description == '0':
        short_description = None
        await state.update_data(short_description=short_description)
        await message.answer("Описание пропущено. Введите текст задачки (например, отрывок кода).")
        logging.info("Пользователь пропустил ввод краткого описания.")
    else:
        await state.update_data(short_description=short_description)
        await message.answer("Описание добавлено. Введите текст задачки (например, отрывок кода).")
        logging.info(f"Краткое описание добавлено: {short_description}")


    # Обновляем состояние FSM
    await state.update_data(short_description=short_description)
    await state.set_state(QuizStates.waiting_for_question)






@quiz_router.message(QuizStates.waiting_for_question)
async def process_question(message: types.Message, state: FSMContext):
    """
    Обработчик ввода текста задачки.
    """
    task_text = message.text.strip()
    logging.info(f"Текст задачки: {task_text}")
    await state.update_data(question=task_text)

    logo_path = "assets/logo.png"
    image = generate_console_image(task_text, logo_path)
    logging.info("Изображение с задачей сгенерировано.")

    temp_file_path = "task_image.png"
    image.save(temp_file_path)

    try:
        await message.answer_photo(types.FSInputFile(temp_file_path))
        logging.info("Изображение отправлено пользователю.")
        await message.answer("Изображение задачи успешно сгенерировано. Введите 4 варианта ответа через запятую.")
    except Exception as e:
        logging.error(f"Ошибка при отправке изображения: {e}")
        await message.answer(f"Ошибка при отправке изображения: {str(e)}")
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            logging.info("Временный файл изображения удалён.")

    await state.set_state(QuizStates.waiting_for_answers)




@quiz_router.message(QuizStates.waiting_for_answers)
async def process_answers(message: types.Message, state: FSMContext):
    """
    Обработчик ввода вариантов ответов.
    """
    answers = [a.strip() for a in message.text.split(',')]
    logging.info(f"Введённые варианты ответа: {answers}")

    if len(answers) != 4:
        await message.answer("Ошибка: Введите ровно 4 варианта ответа.")
        return

    answers.append("Я не знаю, но хочу узнать")
    await state.update_data(answers=answers)
    await message.answer("Варианты ответа сохранены. Укажите правильный ответ.")
    await state.set_state(QuizStates.waiting_for_correct_answer)




@quiz_router.message(QuizStates.waiting_for_correct_answer)
async def process_correct_answer(message: types.Message, state: FSMContext):
    """
    Обработчик ввода правильного ответа.
    """
    correct_answer = message.text.strip()
    data = await state.get_data()

    if correct_answer not in data['answers']:
        await message.answer("Ошибка: Правильный ответ должен быть одним из введённых вариантов.")
        return

    await state.update_data(correct_answer=correct_answer)
    await message.answer("Правильный ответ сохранён. Введите краткое пояснение к задачке.")
    await state.set_state(QuizStates.waiting_for_explanation)




@quiz_router.message(QuizStates.waiting_for_explanation)
async def process_explanation(message: types.Message, state: FSMContext):
    """
    Обработчик ввода пояснения к задачке.
    """
    explanation = message.text.strip()
    await state.update_data(explanation=explanation)
    await message.answer("Пояснение сохранено. Введите ссылку на дополнительный ресурс.")
    await state.set_state(QuizStates.waiting_for_resource_link)





@quiz_router.message(QuizStates.waiting_for_resource_link)
async def process_resource_link(message: types.Message, state: FSMContext):
    """
    Обработчик ввода ссылки на ресурс.
    """
    resource_link = message.text.strip()

    if not is_valid_url(resource_link):
        await message.answer("Ошибка: Введите корректную ссылку.")
        return

    data = await state.get_data()
    temp_file_path = "temp_task_image.png"

    image = generate_console_image(data['question'], "assets/logo.png")
    image.save(temp_file_path)
    await state.update_data(resource_link=resource_link, temp_image_path=temp_file_path)

    quiz_text = (
        f"Тема: {data['topic']}\n"
        f"Подтема: {data.get('subtopic', 'Без подтемы')}\n\n"  # Если подтемы нет, показываем "Без подтемы"
        f"Варианты ответов:\n\n"
        f"1. {data['answers'][0]}\n"
        f"2. {data['answers'][1]}\n"
        f"3. {data['answers'][2]}\n"
        f"4. {data['answers'][3]}\n"
        f"5. Я не знаю, но хочу узнать\n\n"
        f"Ссылка на ресурс: {resource_link}"
    )

    try:
        await message.answer_photo(photo=types.FSInputFile(temp_file_path), caption=quiz_text, reply_markup=get_confirmation_keyboard())
        logging.info("Изображение и текст отправлены с кнопками подтверждения.")
        await message.answer("Задача готова к подтверждению. Выберите, что делать: запустить или отменить.")
    except Exception as e:
        logging.error(f"Ошибка при отправке изображения: {e}")
        await message.answer(f"Ошибка при отправке изображения: {str(e)}")

    await state.set_state(QuizStates.confirming_quiz)





@quiz_router.callback_query(lambda query: query.data == "confirm_launch")
async def confirm_quiz(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    """
    Обработчик подтверждения публикации опроса.
    """
    data = await state.get_data()

    # Генерация имени для изображения
    image_name = generate_image_name(data['topic'])

    try:
        # Загрузка изображения в S3
        image_url = upload_to_s3(Image.open(data['temp_image_path']), image_name)
        logging.info(f"Изображение успешно загружено в S3: {image_url}")

        # Обновление состояния с URL изображения
        await state.update_data(image_url=image_url)
    except Exception as e:
        logging.error(f"Ошибка при загрузке изображения в S3: {e}")
        await callback.message.answer("Ошибка при загрузке изображения.")
        return

    # Отправляем изображение пользователю
    try:
        await callback.message.answer_photo(photo=image_url)
        logging.info("Картинка отправлена пользователю.")
    except Exception as e:
        logging.error(f"Ошибка при отправке изображения: {e}")

    # Отправляем викторину пользователю
    try:
        await callback.message.answer_poll(
            question="Какой вывод верный?",
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
        logging.error(f"Ошибка при отправке викторины: {e}")

    # Сохранение задачи в базу данных
    try:
        new_task = Task(
            topic=data['topic'],
            subtopic=data.get('subtopic', ''),
            question=data['question'],
            correct_answer=data['correct_answer'],
            wrong_answers=",".join([a for a in data['answers'] if a != data['correct_answer']]),
            explanation=data['explanation'],
            resource_link=data['resource_link'],
            image_url=image_url,  # Используем URL изображения
            short_description=data.get('short_description')  # Сохраняем описание
        )
        session.add(new_task)
        await session.commit()
        logging.info(f"Задача сохранена в базе данных: {new_task.id}")
    except Exception as e:
        logging.error(f"Ошибка при сохранении задачи в базе данных: {e}")

    # Очистка временного файла изображения
    if os.path.exists(data['temp_image_path']):
        os.remove(data['temp_image_path'])
        logging.info("Временный файл изображения удалён.")

    # Очищаем состояние
    await callback.message.answer("Викторина успешно запущена.")
    await callback.message.edit_reply_markup(reply_markup=get_task_or_json_keyboard())
    await state.clear()





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
    await callback.message.edit_reply_markup(reply_markup=get_task_or_json_keyboard())
    await state.clear()


@quiz_router.callback_query(lambda query: query.data == "new_task")
async def start_new_quiz(callback: types.CallbackQuery, state: FSMContext):
    logging.info("Кнопка 'Новая задача' была нажата.")
    await callback.message.answer(
        "Выберите тему для новой задачи:",
        reply_markup=topic_keyboard()
    )
    await state.set_state(QuizStates.waiting_for_topic)

    # Возврат к главному меню после завершения действия
    await callback.message.answer(
        "Возвращаемся в главное меню...",
        reply_markup=main_menu_keyboard()
    )




@quiz_router.callback_query(lambda query: query.data == "upload_json")
async def upload_tasks_via_json(callback: types.CallbackQuery, state: FSMContext):
    """
    Обработчик для загрузки задач из JSON файла.
    """
    await callback.message.answer("Пожалуйста, загрузите JSON файл с задачами.")
    await state.set_state(QuizStates.waiting_for_file)
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
        tasks = json.load(file_buffer)
        logging.info(f"Загружено задач: {len(tasks)}")

        for task in tasks:
            # Генерация изображения для каждой задачи
            image = generate_console_image(task['question'], "assets/logo.png")
            image_name = generate_image_name(task['topic'])
            image_url = upload_to_s3(image, image_name)

            # Получаем описание задачи, если оно есть
            short_description = task.get('short_description', None)

            # Сохраняем задачу в базу данных
            new_task = Task(
                topic=task['topic'],
                subtopic=task.get('subtopic', ''),  # Обработайте подтему, если она есть
                question=task['question'],
                correct_answer=task['correct_answer'],
                wrong_answers=",".join([a for a in task['answers'] if a != task['correct_answer']]),
                explanation=task['explanation'],
                resource_link=task['resource_link'],
                image_url=image_url,
                short_description=short_description  # Сохраняем описание задачи
            )
            session.add(new_task)

        # Коммитим транзакцию
        await session.commit()
        logging.info(f"Все задачи сохранены в базу данных.")
        await message.answer(f"Загружено задач: {len(tasks)}")

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
    # Логика отмены викторины
    await callback.message.answer("Викторина отменена.")

    # Замена кнопок на "Новая задача" и "JSON с задачками"
    await callback.message.edit_reply_markup(reply_markup=get_task_or_json_keyboard())
    await state.clear()
