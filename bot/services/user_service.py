# from datetime import datetime
# import logging
#
# from sqlalchemy.ext.asyncio import AsyncSession
# from database.models import User
#
#
#
#
#
#
#
# async def add_user_if_not_exists(user_data, session: AsyncSession):
#     try:
#         # Проверка наличия пользователя в базе данных
#         existing_user = await session.get(User, user_data.id)
#         if existing_user:
#             # Обновление данных пользователя, если он уже существует
#             existing_user.username = user_data.username
#             existing_user.language = user_data.language_code
#         else:
#             # Добавить нового пользователя
#             async with session.begin():  # Используем асинхронный контекстный менеджер для транзакции
#                 new_user = User(
#                     telegram_id=user_data.id,
#                     username=user_data.username,
#                     subscription_status='active',
#                     created_at=datetime.utcnow().replace(tzinfo=None),  # Убираем временную зону
#                     language=user_data.language_code
#                 )
#                 session.add(new_user)
#                 await session.flush()  # Сохраняем изменения
#
#         # Фиксируем изменения
#         await session.commit()
#         logging.info(f"Пользователь {user_data.id} добавлен или обновлен в базе данных.")
#
#     except Exception as e:
#         logging.error(f"Ошибка при добавлении нового пользователя {user_data.id} в базу данных: {e}")
#         await session.rollback()