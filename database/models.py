from sqlalchemy import Column, Integer, String, Text, JSON, ForeignKey, Boolean, DateTime, BigInteger
from sqlalchemy.orm import relationship
from database.base import Base
from datetime import datetime
from datetime import datetime, timezone



def get_current_time():
    return datetime.now(timezone.utc)


class Task(Base):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True)
    topic = Column(String, nullable=False)
    subtopic = Column(String, nullable=True)
    question = Column(String, nullable=False)
    correct_answer = Column(String, nullable=False)
    wrong_answers = Column(JSON, nullable=False)
    explanation = Column(String, nullable=True)
    resource_link = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    short_description = Column(String, nullable=True)
    published = Column(Boolean, default=False, nullable=False)
    publish_date = Column(DateTime, nullable=True)
    group_id = Column(BigInteger, ForeignKey('groups.group_id'), nullable=True)
    language = Column(String, nullable=True)  # Язык по умолчанию
    default_language = Column(String, nullable=False, default='ru')
    translations = relationship('TaskTranslation', back_populates='task', cascade="all, delete-orphan")
    statistics = relationship('TaskStatistics', back_populates='task', cascade="all, delete-orphan")


class TaskTranslation(Base):
    __tablename__ = 'task_translations'

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey('tasks.id'), nullable=False)
    language = Column(String, nullable=False)
    subtopic = Column(String, nullable=True)
    question = Column(String, nullable=False)
    answers = Column(JSON, nullable=False)
    correct_answer = Column(String, nullable=False)
    wrong_answers = Column(JSON, nullable=False)
    explanation = Column(String, nullable=True)

    task = relationship('Task', back_populates='translations')


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String, nullable=True)
    subscription_status = Column(String, default='inactive', nullable=False)
    created_at = Column(DateTime, default=get_current_time, nullable=False)
    language = Column(String, nullable=True)

    statistics = relationship('TaskStatistics', back_populates='user', cascade="all, delete-orphan")


class TaskStatistics(Base):
    __tablename__ = 'task_statistics'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    task_id = Column(Integer, ForeignKey('tasks.id'), nullable=False)
    attempts = Column(Integer, default=0, nullable=False)
    successful = Column(Boolean, default=False, nullable=False)
    last_attempt_date = Column(DateTime, nullable=True)

    user = relationship('User', back_populates='statistics')
    task = relationship('Task', back_populates='statistics')


class Group(Base):
    __tablename__ = 'groups'

    id = Column(Integer, primary_key=True)
    group_name = Column(String, nullable=False)
    group_id = Column(BigInteger, unique=True, nullable=False)
    topic = Column(String, nullable=False)
    language = Column(String, nullable=False)  # Добавляем поле языка