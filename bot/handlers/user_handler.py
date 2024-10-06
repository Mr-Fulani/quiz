# import logging
#
# from aiogram import types, F
# from aiogram import Router
# from aiogram.filters import Command
# from aiogram.types import Message, InlineKeyboardButton
# from aiogram.utils.keyboard import InlineKeyboardBuilder
# from sqlalchemy.ext.asyncio import AsyncSession
#
# from bot.keyboards.inline import topic_keyboard
# from bot.services.user_service import add_user_if_not_exists  # Импортируем сервис для добавления пользователя
# from config import ALLOWED_USERS
# from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
#
#
#
# user_router = Router()
#
#
#
# # Функция для создания клавиатуры
# def main_menu_reply_keyboard():
#     # Создаем кнопки
#     button1 = KeyboardButton(text="Создать задачу")
#     button2 = KeyboardButton(text="Загрузить JSON")
#     button3 = KeyboardButton(text="Показать задачи")
#
#     # Создаем клавиатуру и добавляем кнопки
#     keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
#     keyboard.add(button1, button2, button3)  # Можно добавлять кнопки через запятую или в несколько строк
#
#     return keyboard
#
#
# # Использование в обработчике
# @user_router.message(Command("start"))
# async def start_command(message: Message):
#     await message.answer(
#         "Выберите действие:",
#         reply_markup=main_menu_reply_keyboard()
#     )
#
#
#
#
#
#
# # @user_router.message(Command("start"))
# # async def start_command(message: Message):
# #     # Отображаем главное меню
# #     await message.answer(
# #         "Добро пожаловать! Выберите действие:",
# #         reply_markup=main_menu_keyboard()
# #     )
# #     logging.info("Отправлено главное меню.")
#
#
#


# import logging
# from aiogram import Router, F, types
# from aiogram.filters import Command
# from aiogram.types import Message
#
# from bot.main import main_menu_reply_keyboard, start_router

# from bot.keyboards.inline import main_menu_keyboard  # Импортируем функцию клавиатуры

# Импорт функции для создания главного меню
# from bot.keyboards.reply import main_menu_keyboard
#
#
#
# user_router = Router()
#
#
#
#
# # Обработчик для команды /start
# @user_router.message(Command("start"))
# async def start_command(message: Message):
#     await message.answer(
#         "Выберите действие:",
#         reply_markup=main_menu_keyboard()
#     )
#     logging.info("Отправлено главное меню.")
#
#
#
# # Обработчик для кнопки "Создать задачу"
# @user_router.callback_query(F.data == "new_task")
# async def handle_create_task(callback_query: types.CallbackQuery):
#     await callback_query.message.answer("Вы выбрали 'Создать задачу'.")  # Здесь добавьте логику создания задачи
#
#
#
# # Обработчик для кнопки "Загрузить JSON"
# @user_router.callback_query(F.data == "upload_json")
# async def handle_upload_json(callback_query: types.CallbackQuery):
#     await callback_query.message.answer("Загрузка JSON файла.")  # Здесь добавьте логику загрузки JSON
#
#
#
# # Обработчик для кнопки "Показать задачи"
# @user_router.callback_query(F.data == "show_tasks")
# async def handle_show_tasks(callback_query: types.CallbackQuery):
#     await callback_query.message.answer("Задачи будут показаны.")  # Здесь добавьте логику показа задач
#
#
#
# # Обработчик для кнопки "Дополнительные опции"
# @user_router.callback_query(F.data == "extra_options")
# async def handle_extra_options(callback_query: types.CallbackQuery):
#     await callback_query.message.answer("Здесь будут дополнительные опции.")  # Добавьте логику для дополнительных опций




# @start_router.message(Command("start"))
# async def start_command(message: Message):
#     await message.answer(
#         "Добро пожаловать! Выберите действие:",
#         reply_markup=main_menu_reply_keyboard()  # Используем ReplyKeyboardMarkup
#     )
#     logging.info("Отправлено главное меню.")






import logging
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

# Импорт функции для создания главного меню
from bot.keyboards.reply import main_menu_keyboard
from database.database import add_user_if_not_exists



user_router = Router()


@user_router.message(Command("start"))
async def start_command(message: Message):
    await message.answer(
        "Привет! Выберите действие:",
        reply_markup=main_menu_keyboard()  # Отображение клавиатуры под строкой ввода
    )
    logging.info("Отправлено главное меню.")



@user_router.message(Command("register"))
async def register_user(message: Message, session: AsyncSession):
    # Обработка регистрации пользователя
    await add_user_if_not_exists(message.from_user, session)
    await message.answer("Ваши данные обновлены в системе.")
