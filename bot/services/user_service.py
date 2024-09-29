from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User




async def add_user_if_not_exists(user_data, session: AsyncSession):
    user_id = user_data.id
    username = user_data.username

    # Проверяем, есть ли уже такой пользователь в базе данных
    existing_user = await session.get(User, user_id)
    if existing_user:
        return  # Пользователь уже существует, ничего не делаем

    # Если пользователя нет, добавляем его в базу данных
    new_user = User(
        telegram_id=user_id,
        username=username,
        subscription_status='active'
    )

    session.add(new_user)
    await session.commit()