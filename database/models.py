from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import declarative_base



Base = declarative_base()








class Task(Base):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True)
    topic = Column(String, nullable=False)
    subtopic = Column(String, nullable=True)  # Поле подтемы также необязательное
    question = Column(Text, nullable=False)
    correct_answer = Column(String, nullable=False)
    wrong_answers = Column(Text, nullable=False)  # Список неправильных ответов
    explanation = Column(Text, nullable=False)    # Пояснение обязательное
    resource_link = Column(String, nullable=True) # Ссылка на дополнительный ресурс
    image_url = Column(String, nullable=True)     # URL изображения
    short_description = Column(Text, nullable=True)  # Делаем поле краткого описания необязательным


