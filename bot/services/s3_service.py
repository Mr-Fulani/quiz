import boto3
import io
from PIL import Image
from config import S3_BUCKET_NAME, S3_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY

# Настройка клиента S3
s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=S3_REGION
)


def upload_to_s3(image: Image, image_name: str) -> str:
    """
    Загружает изображение в S3 и возвращает URL.

    :param image: Объект изображения PIL.
    :param image_name: Имя изображения для сохранения в S3.
    :return: URL загруженного изображения или None при ошибке.
    """
    try:
        # Преобразуем изображение в байты
        image_bytes = io.BytesIO()
        image.save(image_bytes, format='PNG')
        image_bytes.seek(0)

        # Загружаем изображение в S3
        response = s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=image_name,
            Body=image_bytes,
            ContentType='image/png',
            ACL='public-read'  # Обеспечивает публичный доступ к объекту
        )

        # Логирование ответа от S3
        print(f"S3 Response: {response}")

        # Проверяем, есть ли успешный ответ от S3
        if response.get('ResponseMetadata', {}).get('HTTPStatusCode') == 200:
            # Формируем URL загруженного изображения
            image_url = f"https://{S3_BUCKET_NAME}.s3.{S3_REGION}.amazonaws.com/{image_name}"
            print(f"Image successfully uploaded to: {image_url}")
            return image_url
        else:
            print(f"Ошибка загрузки изображения в S3: {response}")
            return None

    except Exception as e:
        print(f"Ошибка при загрузке изображения в S3: {e}")
        return None


# # Тестовая функция для проверки загрузки
# def test_upload_to_s3():
#     """
#     Тестовая функция для загрузки изображения в S3.
#     """
#     image = Image.new('RGB', (100, 100), color='red')  # Генерация тестового изображения
#     image_name = "test_image.png"  # Имя файла
#     url = upload_to_s3(image, image_name)  # Вызов функции загрузки
#     if url:
#         print(f"Тестовая загрузка успешна! URL: {url}")
#     else:
#         print("Ошибка при тестовой загрузке")
#
#
# # Вызываем тестовую функцию
# if __name__ == "__main__":
#     test_upload_to_s3()
