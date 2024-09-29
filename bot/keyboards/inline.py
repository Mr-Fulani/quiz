from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


# Клавиатура выбора темы
def topic_keyboard():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Python", callback_data="topic_python"))
    builder.add(InlineKeyboardButton(text="SQL", callback_data="topic_sql"))
    builder.add(InlineKeyboardButton(text="Django", callback_data="topic_django"))
    builder.add(InlineKeyboardButton(text="ORM", callback_data="topic_orm"))
    return builder.as_markup()


# Клавиатура подтверждения публикации
def get_confirmation_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Запустить", callback_data="confirm_launch"))
    builder.add(InlineKeyboardButton(text="Отменить", callback_data="confirm_cancel"))
    return builder.as_markup()


# Клавиатура выбора действия после публикации
def get_task_or_json_keyboard():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Новая задача", callback_data="new_task"))
    builder.add(InlineKeyboardButton(text="JSON с задачами", callback_data="upload_json"))
    return builder.as_markup()


# Клавиатура отправки в группу
def get_publish_group_keyboard():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Отправить в группу", callback_data="publish_to_group"))
    builder.add(InlineKeyboardButton(text="Отменить", callback_data="confirm_cancel"))  # Добавляем кнопку "Отменить"
    return builder.as_markup()


# Основное меню
def main_menu_keyboard():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Создать задачу", callback_data="new_task"))
    builder.add(InlineKeyboardButton(text="Загрузить JSON", callback_data="upload_json"))
    builder.add(InlineKeyboardButton(text="Показать задачи", callback_data="show_tasks"))
    return builder.as_markup()