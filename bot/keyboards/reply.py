from aiogram.types import ReplyKeyboardMarkup, KeyboardButton




# Функция для создания главного меню
def main_menu_keyboard() -> ReplyKeyboardMarkup:
    # Создаем кнопки
    button1 = KeyboardButton(text="Создать задачу")
    button2 = KeyboardButton(text="Загрузить JSON")
    button3 = KeyboardButton(text="Опубликовать по ID")
    button4 = KeyboardButton(text="Опубликовать все задачи")

    # Создаем клавиатуру и добавляем кнопки в один или несколько рядов
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [button1, button2],  # Первый ряд кнопок
            [button3, button4]  # Второй ряд кнопок
        ],
        resize_keyboard=True  # Опциональный параметр для изменения размера кнопок
    )

    return keyboard


