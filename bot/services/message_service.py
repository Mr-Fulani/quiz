import asyncio
import logging
from aiogram import Bot
from aiogram.exceptions import TelegramRetryAfter, TelegramServerError


async def send_message_with_retry(bot: Bot, chat_id: int, text: str):
    """
    Отправляет сообщение в чат с повторной попыткой в случае возникновения ошибок.

    :param bot: Экземпляр бота для отправки сообщений.
    :param chat_id: ID чата, в который отправляется сообщение.
    :param text: Текст сообщения.
    """
    tries = 0
    max_retries = 5

    while tries < max_retries:
        try:
            await bot.send_message(chat_id, text)
            break  # Если отправка успешна, выходим из цикла

        except TelegramRetryAfter as e:
            # Если Telegram сообщает о превышении лимита, ждем указанное количество секунд
            logging.warning(f"Too Many Requests: нужно подождать {e.retry_after} секунд.")
            await asyncio.sleep(e.retry_after)

        except TelegramServerError:
            # Если возникает ошибка сервера Telegram, увеличиваем время ожидания перед повторной попыткой
            logging.error("Ошибка на сервере Telegram. Ждем перед повторной отправкой...")
            await asyncio.sleep(2 ** tries)  # Экспоненциальное увеличение задержки

        except Exception as e:
            # Обработка любых других ошибок
            logging.error(f"Неожиданная ошибка: {e}")
            break  # Выход из цикла при других непредвиденных ошибках

        tries += 1

    else:
        logging.error(f"Не удалось отправить сообщение после {max_retries} попыток.")




async def send_photo_with_retry(bot: Bot, chat_id: int, photo, caption=None):
    """
    Отправляет фотографию в чат с повторной попыткой в случае возникновения ошибок.

    :param bot: Экземпляр бота для отправки фотографий.
    :param chat_id: ID чата, в который отправляется фотография.
    :param photo: Содержимое фотографии или URL.
    :param caption: Описание к фотографии (опционально).
    """
    tries = 0
    max_retries = 5

    while tries < max_retries:
        try:
            await bot.send_photo(chat_id, photo, caption=caption)
            break

        except TelegramRetryAfter as e:
            logging.warning(f"Too Many Requests: нужно подождать {e.retry_after} секунд.")
            await asyncio.sleep(e.retry_after)

        except TelegramServerError:
            logging.error("Ошибка на сервере Telegram. Ждем перед повторной отправкой...")
            await asyncio.sleep(2 ** tries)

        except Exception as e:
            logging.error(f"Неожиданная ошибка: {e}")
            break

        tries += 1

    else:
        logging.error(f"Не удалось отправить фотографию после {max_retries} попыток.")