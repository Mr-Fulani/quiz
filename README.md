# quiz
### Документация по проекту Telegram-бота (Русский)

---

## Описание проекта

Проект представляет собой Telegram-бота для публикации программных задач и викторин в различные Telegram-каналы и группы. Бот предоставляет следующие основные функции:

1. Создание задач по программированию через интерфейс Telegram.
2. Публикация задач с изображениями и викторинами в виде опросов в выбранные группы.
3. Управление подписками пользователей для предоставления доступа к расширенным функциям.
4. Загрузка задач через JSON-файлы для массового добавления задач в базу данных.
5. Поддержка нескольких тематических каналов и групп, разделенных по направлениям (например, Python, JavaScript и т.д.).

Проект использует библиотеку **`aiogram`** для работы с Telegram API и асинхронного взаимодействия с пользователями. Все данные, включая задачи, пользователей и статистику, хранятся в базе данных.

---

## Компоненты проекта

### 1. Структура базы данных

Для хранения данных бот использует базу данных с несколькими таблицами:

#### Таблица `users`

Хранит информацию о пользователях бота, их статус подписки и другую необходимую информацию.

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,  -- Telegram ID пользователя
    username VARCHAR(255),               -- Имя пользователя в Telegram
    first_name VARCHAR(255),             -- Имя пользователя
    last_name VARCHAR(255),              -- Фамилия пользователя
    created_at TIMESTAMP DEFAULT NOW(),  -- Дата регистрации
    subscription_status BOOLEAN DEFAULT FALSE  -- Статус подписки (есть или нет)
);
```

#### Таблица `tasks`

Хранит задачи, которые создаются и публикуются в Telegram. Каждая задача имеет вопрос, варианты ответов, правильный ответ, а также дополнительную информацию.

```sql
CREATE TABLE tasks (
    id SERIAL PRIMARY KEY,
    topic VARCHAR(255),                   -- Тема задачи (например, Python, SQL)
    subtopic VARCHAR(255),                -- Подтема задачи (например, циклы, функции)
    question TEXT,                        -- Вопрос (сама задача)
    correct_answer TEXT,                  -- Правильный ответ
    wrong_answers JSONB,                  -- Неправильные ответы (хранятся как JSON)
    explanation TEXT,                     -- Объяснение правильного ответа
    resource_link TEXT,                   -- Ссылка на дополнительный ресурс
    image_url TEXT,                       -- Ссылка на изображение задачи
    short_description TEXT                -- Краткое описание задачи
);
```

---

## Основные функции бота

### 1. Создание задач

Пользователь может взаимодействовать с ботом через чат, создавая задачи шаг за шагом. Процесс выглядит следующим образом:

- Пользователь выбирает тему задачи (например, Python).
- Затем вводит подтему (например, "Циклы") и краткое описание задачи.
- После этого бот запрашивает текст вопроса и варианты ответов (правильный и неправильные).
- Пользователь вводит объяснение правильного ответа и ссылку на дополнительный ресурс (если есть).
- Все данные сохраняются в базе, а затем задача может быть опубликована в группу.

**Пример взаимодействия**:

1. Выбор темы: "Python"
2. Ввод подтемы: "Списки"
3. Ввод вопроса: "Что делает функция append?"
4. Ввод вариантов ответов:
   - "Добавляет элемент в конец списка" (правильный ответ)
   - "Удаляет элемент из списка"
   - "Изменяет порядок элементов"
   - "Очищает список"
5. Ввод объяснения: "Функция append добавляет новый элемент в конец списка."
6. Ввод ссылки: "https://python.org/docs"

### 2. Публикация задач в группы

Бот поддерживает публикацию задач в различные Telegram-группы или каналы, в зависимости от их тематики. После создания задачи пользователь может выбрать, в какую группу её отправить. Например, задачи по Python публикуются в группу, посвященную Python.

Процесс публикации состоит из двух этапов:
- Отправка изображения задачи с кратким описанием.
- Отправка викторины в формате опроса с вариантами ответов.

### 3. Управление подписками пользователей

Для доступа к расширенному функционалу (например, эксклюзивным задачам или статистике) пользователи могут оформить подписку. Бот проверяет статус подписки перед предоставлением доступа к определённым функциям.

### 4. Загрузка задач через JSON

Бот поддерживает массовую загрузку задач через JSON-файлы. Администратор может загрузить файл с задачами, и все они будут автоматически сохранены в базе данных. Это полезно для быстрой добавки большого количества задач.

---

## Основные команды

- **/start**  
  Приветствует пользователя и регистрирует его в системе, если он ещё не был зарегистрирован.

- **/new_task**  
  Начинает процесс создания новой задачи.

- **/upload_json**  
  Позволяет загрузить JSON-файл с задачами.

- **/subscription**  
  Проверяет статус подписки пользователя.

- **/help**  
  Показывает список доступных команд и информацию о том, как использовать бота.

### Встроенные кнопки:

- **Запустить**  
  Подтверждает и публикует задачу.

- **Отправить в группу**  
  Отправляет задачу в выбранную группу.

- **Отменить**  
  Отменяет текущую задачу или действие.

---

## Возможные улучшения

1. **Добавление статистики пользователей**: отслеживание того, как пользователи взаимодействуют с задачами и какие задачи были решены.

2. **Многоуровневая система публикации**: поддержка нескольких групп для различных тем, где каждая группа или канал получает задачи только по конкретной тематике.

3. **Уведомления о подписке**: добавление функции уведомлений о продлении подписки и интеграция с платёжными системами для автоматического продления.

---

### Project Documentation (English)

---

## Project Overview

This project is a Telegram bot designed for publishing programming quizzes and tasks to various Telegram channels and groups. The main functionalities include:

1. Task creation via Telegram's chat interface.
2. Publishing tasks with images and quizzes as polls to selected groups.
3. Managing user subscriptions for premium features access.
4. Uploading tasks via JSON files for bulk additions to the database.
5. Support for multiple thematic channels and groups (e.g., Python, JavaScript).

The bot is built using the **`aiogram`** library for asynchronous interaction with the Telegram API, and it stores all data, including tasks, users, and statistics, in a database.

---

## Project Components

### 1. Database Structure

The bot uses a database with several tables to store information:

#### Table `users`

Stores information about users of the bot, including their subscription status.

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,  -- User's Telegram ID
    username VARCHAR(255),               -- Telegram username
    first_name VARCHAR(255),             -- User's first name
    last_name VARCHAR(255),              -- User's last name
    created_at TIMESTAMP DEFAULT NOW(),  -- Registration date
    subscription_status BOOLEAN DEFAULT FALSE  -- Subscription status (active or not)
);
```

#### Table `tasks`

Stores tasks created and published in Telegram. Each task has a question, answer options, the correct answer, and additional information.

```sql
CREATE TABLE tasks (
    id SERIAL PRIMARY KEY,
    topic VARCHAR(255),                   -- Task topic (e.g., Python, SQL)
    subtopic VARCHAR(255),                -- Task subtopic (e.g., loops, functions)
    question TEXT,                        -- Task question
    correct_answer TEXT,                  -- Correct answer
    wrong_answers JSONB,                  -- Incorrect answers (stored as JSON)
    explanation TEXT,                     -- Explanation for the correct answer
    resource_link TEXT,                   -- Link to additional resource
    image_url TEXT,                       -- Task image URL
    short_description TEXT                -- Short task description
);
```

---

## Main Bot Functions

### 1. Task Creation

Users interact with the bot through the chat interface to create tasks step by step. The process looks like this:

- The user selects the task's topic (e.g., Python).
- Then, the subtopic (e.g., "Loops") and a short description are entered.
- Afterward, the bot asks for the question text and answer options (correct and incorrect).
- The user enters an explanation for the correct answer and a link to a resource (if available).
- All data is saved in the database, and the task can be published to a group.

**Example interaction**:

1. Select a topic: "Python"
2. Enter subtopic: "Lists"
3. Enter question: "What does the append function do?"
4. Enter answer options:
   - "Adds an element to the end of the list" (correct answer)
   - "Removes an element from the list"
   - "Changes the order of elements"
   - "Clears the list"
5. Enter explanation: "The append function adds a new element to the end of the list."
6. Enter link: "https://python.org/docs"

### 2. Task Publication to Groups

The bot supports publishing tasks to different Telegram groups or channels depending on their topic.