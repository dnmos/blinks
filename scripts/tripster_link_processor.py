import os
import json
from dotenv import load_dotenv
import core.wp_api_utils
import core.tripster_data_extractor
import logging
import requests
import time
import pymysql

# Импортируем функции для работы с БД из db.py
from db import db

load_dotenv()

# Настройка логирования
DEFAULT_LOG_LEVEL = logging.INFO
logging.basicConfig(level=DEFAULT_LOG_LEVEL, format='%(asctime)s - %(levelname)s - %(message)s')

TRIPSTER_DOMAIN = os.getenv("TRIPSTER_DOMAIN", "tripster.ru")
MAX_RETRIES = int(os.getenv("MAX_RETRIES", 3))
RETRY_DELAY = int(os.getenv("RETRY_DELAY", 2))


def fetch_wordpress_post(api_url, post_id, max_retries=3, retry_delay=2):
    """
    Получает данные поста по его ID из API WordPress с повторными попытками.

    Args:
        api_url (str): URL API WordPress.
        post_id (int): ID поста.
        max_retries (int): Максимальное количество попыток.
        retry_delay (int): Задержка между попытками в секундах.

    Returns:
        dict: Данные поста в формате JSON или None в случае ошибки.
    """
    for attempt in range(max_retries):
        try:
            response = requests.get(f"{api_url}/{post_id}")
            response.raise_for_status()  # Проверяем статус код ответа

            # Явно декодируем контент в UTF-8
            try:
                content = response.json()
            except Exception as e:
                logging.error(f"Ошибка при декодировании JSON для поста с ID {post_id}: {e}")
                return None
            return content
        except requests.exceptions.RequestException as e:
            logging.error(f"Ошибка requests при получении поста с ID {post_id}, попытка {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay ** (attempt + 1))  # Экспоненциальная задержка
            else:
                logging.error(f"Превышено максимальное количество попыток для поста с ID {post_id}")
                return None
        except Exception as e:
            logging.error(f"Непредвиденная ошибка при получении поста с ID {post_id}, попытка {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay ** (attempt + 1))  # Экспоненциальная задержка
            else:
                logging.error(f"Превышено максимальное количество попыток для поста с ID {post_id}")
                return None

    return None


def save_tripster_data(post_id, post_title, link_type, data):
    """Сохраняет данные о виджете или диплинке в базу данных."""
    record = {
        'post_id': str(post_id),
        'post_title': str(post_title),
        'link_type': link_type,
        'exp_id': str(data.get('anchor') or data.get('id') or ''),
        'exp_title': str(data.get('title') or ''),
        'exp_url': str(data.get('url') or ''),
        'link_status': str(data.get('status') or ''),
        'inactivity_reason': str(data.get('inactivity_reason') or ''),
        'is_unknown_type': data.get('is_unknown_type') if data.get('is_unknown_type') is not None else False
    }
    logging.info(f"Вставляем {link_type}: {record}")
    db.insert_or_update_data(record)


def process_tripster_links():
    """Извлекает и сохраняет виджеты и диплинки из постов WordPress."""
    try:
        post_data_file = core.wp_api_utils.construct_json_file_path(core.wp_api_utils.POST_DATA_FILE)

        with open(post_data_file, 'r', encoding='utf-8') as f:
            post_data = json.load(f)

    except FileNotFoundError as e:
        logging.error(f"Ошибка: Файл {post_data_file} не найден: {e}")
        return
    except json.JSONDecodeError as e:
        logging.error(f"Ошибка: Некорректный JSON в файле {post_data_file}: {e}")
        return
    except Exception as e:
        logging.error(f"Непредвиденная ошибка при чтении файла: {e}")
        return

    if not post_data:
        logging.warning("Нет данных о постах для обработки.")
        return

    for post in post_data:
        post_id = post.get('id')
        post_title = post.get('title')

        if post_id:
            try:
                full_post = fetch_wordpress_post(core.wp_api_utils.API_URL, post_id, MAX_RETRIES, RETRY_DELAY)

                if full_post:
                    content = full_post['content']['rendered']
                    logging.info(f"Обрабатывается пост ID: {post_id}, title: {post_title}")
                    widgets = core.tripster_data_extractor.extract_tripster_widgets(content, TRIPSTER_DOMAIN)
                    deeplinks = core.tripster_data_extractor.extract_deeplinks(content, TRIPSTER_DOMAIN)

                    for widget in widgets:
                        save_tripster_data(post_id, post_title, 'widget', widget)

                    for deeplink in deeplinks:
                        save_tripster_data(post_id, post_title, 'deeplink', deeplink)

                else:
                    logging.warning(f"Не удалось получить данные поста с ID {post_id}.")
            except Exception as e:
                logging.error(f"Ошибка при обработке поста {post_id}: {e}")
        else:
            logging.warning("Ошибка: Не найден ID поста.")

def main():
    """Главная функция, запускает обработку ссылок Tripster."""
    process_tripster_links()


if __name__ == "__main__":
    main()