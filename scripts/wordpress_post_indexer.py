import os
import json
from dotenv import load_dotenv
import core.wp_api_utils
import html
import logging
import requests

load_dotenv()

# Уровень логирования по умолчанию
DEFAULT_LOG_LEVEL = logging.INFO

logging.basicConfig(
    level=DEFAULT_LOG_LEVEL,
    format='%(asctime)s - %(levelname)s - %(message)s',
    # filename=LOG_FILE,  # Убираем пока запись в файл
)


def unescape_html(text):
    """
    Декодирует HTML-сущности в строке.

    Args:
        text (str): Строка для декодирования.

    Returns:
        str: Декодированная строка.  В случае ошибки возвращает исходный текст.
    """
    try:
        return html.unescape(text)
    except Exception as e:
        logging.error(f"Ошибка при декодировании HTML: {e}. Возвращается исходный текст.")
        return text


def process_wordpress_posts():
    """
    Получает и обрабатывает посты из WordPress API, сохраняя их в JSON.
    """
    all_posts = []
    page_number = 1
    api_url = core.wp_api_utils.API_URL  # Получаем URL API

    while True:
        try:
            response = requests.get(f"{api_url}?page={page_number}")
            response.raise_for_status()  # Проверяем статус код ответа

            posts = response.json()
            if not posts:
                logging.info("Нет данных на текущей странице.")
                break

            all_posts.extend(posts)
            total_pages = int(response.headers.get('X-WP-TotalPages', 1))

            logging.info(f"Загружена страница {page_number} из {total_pages}")
            page_number += 1

            if page_number > total_pages:
                break

        except requests.exceptions.RequestException as e:
            logging.error(f"Ошибка при получении данных из API (страница {page_number}): {e}")
            break  # Прерываем цикл при ошибке

        except json.JSONDecodeError as e:
            logging.error(f"Ошибка при разборе JSON (страница {page_number}): {e}")
            break

        except Exception as e:
            logging.error(f"Непредвиденная ошибка при обработке страницы {page_number}: {e}")
            break

    if all_posts:
        logging.info(f"Всего получено {len(all_posts)} постов из API.")

        post_data = []
        for i, post in enumerate(all_posts):
            post_id = post.get('id')
            title = post.get('title', {}).get('rendered', 'Нет заголовка')
            decoded_title = unescape_html(title)
            post_data.append({'order': i + 1, 'id': post_id, 'title': decoded_title})

        try:
            core.wp_api_utils.save_data_to_json_file(post_data)
        except Exception as e:
            logging.error(f"Ошибка при сохранении данных в JSON файл: {e}")
    else:
        logging.warning("Не удалось получить данные из API.")


def main():
    """
    Главная функция, запускает обработку постов WordPress.
    """
    process_wordpress_posts()


if __name__ == "__main__":
    main()