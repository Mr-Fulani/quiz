from aiogram.fsm.state import StatesGroup, State





class QuizStates(StatesGroup):
    waiting_for_short_description = State()
    confirming_quiz = State()  # Ожидание подтверждения сохранения викторины
    waiting_for_topic = State()  # Ожидание выбора темы
    waiting_for_question = State()  # Ожидание ввода вопроса
    waiting_for_answers = State()  # Ожидание ввода вариантов ответов
    waiting_for_correct_answer = State()  # Ожидание указания правильного ответа
    waiting_for_explanation = State()  # Ожидание ввода пояснения
    waiting_for_resource_link = State()  # Ожидание ссылки на ресурс
    waiting_for_file = State()  # Ожидание загрузки файла с задачами (новое состояние)
    waiting_for_post_time = State()
    waiting_for_subtopic = State()