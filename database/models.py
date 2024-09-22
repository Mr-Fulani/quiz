from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import declarative_base



Base = declarative_base()



class Task(Base):
    """
    Модель для хранения вопросов викторины.
    """
    __tablename__ = 'tasks'

    id: int = Column(Integer, primary_key=True)
    topic: str = Column(String, index=True)
    question: str = Column(Text, nullable=False)
    correct_answer: str = Column(String, nullable=False)
    wrong_answers: str = Column(Text, nullable=False)  # Хранение в виде строки или JSON
    explanation: str = Column(Text, nullable=True)
    resource_link: str = Column(Text, nullable=True)
    image_url: str = Column(Text, nullable=True)  # Поле для хранения URL изображения
