import os
import json
from dotenv import load_dotenv
import core.wp_api_utils
import html
import logging

# Настройка базовой конфигурации логирования
logging.basicConfig(
    level=logging.INFO,  # Уровень логирования (можно менять через переменные окружения)
    format='%(asctime)s - %(levelname)s - %(message)s'
)

load_dotenv()


def unescape_html(text):
    """Декодирует HTML-сущности."""
    try:
        return html.unescape(text)
    except Exception as e:
        logging.error(f"Ошибка при декодировании HTML: {e}. Возвращается исходный текст.")
        return text


def process_wordpress_posts():
    """Получает и обрабатывает посты из WordPress API, сохраняя их в JSON."""
    all_posts = []
    page_number = 1
    total_pages = 1

    while page_number <= total_pages:
        try:
            posts, total_pages = core.wp_api_utils.fetch_wordpress_posts(core.wp_api_utils.API_URL, page_number)
        except Exception as e:
            logging.error(f"Ошибка при получении данных из API: {e}")
            break

        if not posts:
            break

        all_posts.extend(posts)
        page_number += 1
        logging.info(f"Загружена страница {page_number - 1} из {total_pages}")

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
    """Главная функция, запускает обработку."""
    process_wordpress_posts()


if __name__ == "__main__":
    main()