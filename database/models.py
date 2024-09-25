from sqlalchemy import Column, Integer, String, Text, JSON
from sqlalchemy.orm import declarative_base
from sqlalchemy.dialects.postgresql import JSONB



Base = declarative_base()





class Task(Base):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True)
    topic = Column(String, nullable=False)
    subtopic = Column(String, nullable=True)  # Поле подтемы также необязательное
    question = Column(Text, nullable=False)
    correct_answer = Column(String, nullable=False)
    wrong_answers = Column(JSONB, nullable=False)  # Поле с неправильными ответами как JSON
    explanation = Column(Text, nullable=False)    # Пояснение обязательно
    resource_link = Column(String, nullable=True)  # Ссылка на ресурс
    image_url = Column(String, nullable=True)     # URL изображения
    short_description = Column(Text, nullable=True)  # Поле краткого описания необязательно
