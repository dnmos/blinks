import os
import json
from dotenv import load_dotenv
import core.wp_api_utils
import core.tripster_data_extractor
import logging
import requests
import html
import time
import pymysql

# Импортируем функции для работы с БД из db.py
from db import db

# Настройка базовой конфигурации логирования
logging.basicConfig(
    level=logging.INFO,  # Уровень логирования (можно менять через переменные окружения)
    format='%(asctime)s - %(levelname)s - %(message)s'
)

load_dotenv()

TRIPSTER_DOMAIN = os.getenv("TRIPSTER_DOMAIN", "tripster.ru")
MAX_RETRIES = int(os.getenv("MAX_RETRIES", 3))
RETRY_DELAY = int(os.getenv("RETRY_DELAY", 2))

# Переменные окружения для БД теперь используются внутри db.py

def fetch_wordpress_post(api_url, post_id, max_retries=3, retry_delay=2):
    """Получает данные поста по его ID из API WordPress с повторными попытками."""
    for attempt in range(max_retries):
        try:
            return core.wp_api_utils.fetch_wordpress_post_by_id(api_url, post_id)
        except requests.exceptions.RequestException as e:
            logging.error(f"Ошибка requests при получении поста с ID {post_id}, попытка {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay ** (attempt + 1))  # Экспоненциальная задержка
            else:
                raise  # Re-raise the exception after max retries
        except json.JSONDecodeError as e:
            logging.error(f"Ошибка JSONDecodeError при получении поста с ID {post_id}, попытка {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay ** (attempt + 1))  # Экспоненциальная задержка
            else:
                raise  # Re-raise the exception after max retries
        except Exception as e:
            logging.error(f"Непредвиденная ошибка при получении поста с ID {post_id}, попытка {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay ** (attempt + 1))  # Экспоненциальная задержка
            else:
                raise  # Re-raise the exception after max retries

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

    for post in post_data[7:8]:
        post_id = post.get('id')
        post_title = post.get('title')

        if post_id:
            try:
                full_post = fetch_wordpress_post(core.wp_api_utils.API_URL, post_id, MAX_RETRIES, RETRY_DELAY)

                if full_post:
                    content = full_post
                    logging.info(f"Обрабатывается пост ID: {post_id}, title: {post_title}")
                    widgets = core.tripster_data_extractor.extract_tripster_widgets(content, TRIPSTER_DOMAIN)
                    deeplinks = core.tripster_data_extractor.extract_deeplinks(content, TRIPSTER_DOMAIN)

                    for widget in widgets:
                        # Создаем словарь с данными для вставки/обновления
                        data = {
                            'post_id': str(post_id),
                            'post_title': str(post_title),
                            'link_type': 'widget',
                            'exp_id': str(widget.get('id') or ''),
                            'exp_title': str(widget.get('title') or ''),
                            'exp_url': str(widget.get('url') or ''),
                            'status': str(widget.get('status') or ''),
                            'inactivity_reason': str(widget.get('inactivity_reason') or ''),
                            'is_unknown_type': widget.get('is_unknown_type') if widget.get('is_unknown_type') is not None else False
                        }
                        # Вставляем или обновляем данные
                        logging.info(f"Вставляем виджет: {data}")
                        db.insert_or_update_data(data)

                    for deeplink in deeplinks:
                        # Создаем словарь с данными для вставки/обновления
                        data = {
                            'post_id': str(post_id),
                            'post_title': str(post_title),
                            'link_type': 'deeplink',
                            'exp_id': str(deeplink.get('anchor') or ''),
                            'exp_title': str(deeplink.get('title') or ''),
                            'exp_url': str(deeplink.get('url') or ''),
                            'status': str(deeplink.get('status') or ''),
                            'inactivity_reason': str(deeplink.get('inactivity_reason') or ''),
                            'is_unknown_type': deeplink.get('is_unknown_type') if deeplink.get('is_unknown_type') is not None else False
                        }
                        # Вставляем или обновляем данные
                        logging.info(f"Вставляем deeplink: {data}")
                        db.insert_or_update_data(data)

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