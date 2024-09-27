import os
import io
import hashlib
import datetime
from uuid import uuid4

from PIL import Image, ImageDraw, ImageFont
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import ImageFormatter
from pygments.styles import get_style_by_name


def get_default_font():
    """
    Возвращает путь к стандартному системному шрифту.
    """
    try:
        return ImageFont.load_default()
    except IOError:
        system_fonts = [
            '/Library/Fonts/Arial.ttf',
            'C:\\Windows\\Fonts\\arial.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        ]
        for font_path in system_fonts:
            if os.path.exists(font_path):
                return font_path
        return None


def generate_console_image(task_text: str, logo_path: str) -> Image.Image:
    """
    Генерирует изображение консоли с подсвеченным кодом задачи и логотипом.

    :param task_text: Текст задачи (код).
    :param logo_path: Путь к логотипу.
    :return: Объект изображения PIL.
    """
    # Размеры изображения и консольного окна
    width, height = 800, 500
    console_width, console_height = 700, 350

    # Создаем изображение с фоном светло-синего цвета
    background_color = (173, 216, 230)  # Светло-синий цвет фона
    image = Image.new("RGB", (width, height), background_color)
    draw = ImageDraw.Draw(image)

    # Цвета для кругов
    red = (255, 59, 48)
    yellow = (255, 204, 0)
    green = (40, 205, 65)

    # Цвет фона для консоли (тёмно-серый)
    console_color = (30, 30, 30)

    # Радиус для овальных углов консоли
    corner_radius = 20

    # Вычисляем центр для консоли
    console_x0 = (width - console_width) // 2
    console_y0 = (height - console_height) // 2
    console_x1 = console_x0 + console_width
    console_y1 = console_y0 + console_height

    # Нарисовать прямоугольник с овальными углами для консоли
    draw.rounded_rectangle((console_x0, console_y0, console_x1, console_y1), radius=corner_radius, fill=console_color)

    # Нарисовать три точки (имитация кнопок) внутри консоли в верхнем левом углу
    circle_radius = 10
    circle_spacing = 15
    circle_y = console_y0 + 15

    for i, color in enumerate([red, yellow, green]):
        draw.ellipse((console_x0 + (2 * i + 1) * circle_spacing,
                      circle_y,
                      console_x0 + (2 * i + 1) * circle_spacing + 2 * circle_radius,
                      circle_y + 2 * circle_radius),
                     fill=color)

    # Динамическое определение размера шрифта
    max_font_size = 24
    min_font_size = 10
    font_size = max_font_size
    padding = 20
    code_width = console_width - 2 * padding
    code_height = console_height - 2 * padding - 30  # 30 - примерная высота кнопок

    while font_size >= min_font_size:
        code_image = highlight(
            task_text,
            PythonLexer(),
            ImageFormatter(
                font_size=font_size,
                style=get_style_by_name('monokai'),
                line_numbers=False,
                image_pad=0,
                line_pad=0,
                background_color=console_color
            )
        )
        code_img = Image.open(io.BytesIO(code_image))
        if code_img.width <= code_width and code_img.height <= code_height:
            break
        font_size -= 1

    # Вставка изображения с кодом
    code_x = console_x0 + padding
    code_y = console_y0 + padding + 30
    image.paste(code_img, (code_x, code_y))

    # Добавление логотипа в правый верхний угол
    try:
        logo = Image.open(logo_path)
        logo.thumbnail((60, 60))  # Изменяем размер логотипа
        logo_x = width - logo.width - 20
        logo_y = 20
        image.paste(logo, (logo_x, logo_y), logo)
    except FileNotFoundError:
        print(f"Логотип не найден по пути: {logo_path}")

    return image


def save_and_show_image(image: Image.Image, filename: str = "console_image.png"):
    """
    Сохраняет изображение на диск и открывает его для просмотра.

    :param image: Объект изображения PIL.
    :param filename: Имя файла для сохранения изображения.
    """
    image.save(filename)
    image.show()


def get_image_bytes(image: Image.Image) -> bytes:
    """
    Преобразует изображение в байты.

    :param image: Объект изображения PIL.
    :return: Байты изображения.
    """
    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()





def generate_image_name(topic: str) -> str:
    """
    Генерирует уникальное название для изображения на основе темы и текущей даты.

    :param topic: Тема вопроса.
    :return: Сгенерированное имя файла.
    """
    # Текущая дата
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    # Формируем название файла: тема и дата
    image_name = f"{topic}_{timestamp}.png"
    return image_name







def generate_image_name(topic):
    unique_id = uuid4().hex
    return f"{topic}_{unique_id}.png"





# # Пример использования
# if __name__ == "__main__":
#     task_text = """
# def hello_world():
#     print("Hello, World!")
#
# hello_world()
#     """
#     logo_path = "assets/logo.png"  # Замените на реальный путь к логотипу
#
#     image = generate_console_image(task_text, logo_path)
#     save_and_show_image(image)
#
#     # Для использования в боте
#     image_bytes = get_image_bytes(image)
#     # Теперь image_bytes можно использовать для отправки через бота



