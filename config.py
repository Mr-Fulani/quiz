import json
import os
from dotenv import load_dotenv


load_dotenv()


BOT_TOKEN = os.getenv("BOT_TOKEN")


S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
S3_REGION = os.getenv("S3_REGION")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")


GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID")   # Укажите ваш chat_id группы
GROUP_CHAT_ID_2 = os.getenv("GROUP_CHAT_ID_2")   # Укажите ваш chat_id группы


DATABASE_URL = os.getenv('DATABASE_URL')


# Получаем ALLOWED_USERS из .env и конвертируем из строки в список
ALLOWED_USERS = json.loads(os.getenv("ALLOWED_USERS", "[]"))
