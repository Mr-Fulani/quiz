from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import declarative_base



Base = declarative_base()






class Task(Base):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True)
    topic = Column(String, index=True, nullable=False)
    subtopic = Column(String, nullable=True)  # Поле подтемы, которое может быть пустым
    question = Column(Text, nullable=False)
    correct_answer = Column(String, nullable=False)
    wrong_answers = Column(Text, nullable=False)  # Храним в виде JSON или строки
    explanation = Column(Text, nullable=True)
    resource_link = Column(Text, nullable=True)
    image_url = Column(Text, nullable=False)

