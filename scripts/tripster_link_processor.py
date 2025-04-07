import os
import json
from dotenv import load_dotenv
import core.wp_api_utils
import core.tripster_data_extractor
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

# Настройка базовой конфигурации логирования
logging.basicConfig(
    level=logging.INFO,  # Уровень логирования (можно менять через переменные окружения)
    format='%(asctime)s - %(levelname)s - %(message)s'
)

load_dotenv()

TRIPSTER_DOMAIN = os.getenv("TRIPSTER_DOMAIN", "tripster.ru")
MAX_RETRIES = int(os.getenv("MAX_RETRIES", 3))
RETRY_DELAY = int(os.getenv("RETRY_DELAY", 2))


@retry(stop=stop_after_attempt(MAX_RETRIES), wait=wait_exponential(multiplier=RETRY_DELAY))
def fetch_wordpress_post_with_retry(api_url, post_id):
    """Получает данные поста по его ID из API WordPress с повторными попытками."""
    return core.wp_api_utils.fetch_wordpress_post_by_id(api_url, post_id)


def process_tripster_links():
    """Извлекает и сохраняет виджеты и диплинки из постов WordPress."""
    try:
        post_data_file = core.wp_api_utils.construct_json_file_path(core.wp_api_utils.POST_DATA_FILE)

        with open(post_data_file, 'r', encoding='utf-8') as f:
            post_data = json.load(f)

    except FileNotFoundError:
        logging.error(f"Ошибка: Файл {post_data_file} не найден.")
        return
    except json.JSONDecodeError as e:
        logging.error(f"Ошибка: Некорректный JSON в файле {post_data_file}.")
        return
    except Exception as e:
        logging.error(f"Непредвиденная ошибка при чтении файла: {e}")
        return

    if not post_data:
        logging.warning("Нет данных о постах для обработки.")
        return

    all_links_data = []

    for post in post_data[7:8]:  # Обрабатываем все посты
        post_id = post.get('id')
        post_title = post.get('title')

        if post_id:
            try:
                full_post = fetch_wordpress_post_with_retry(core.wp_api_utils.API_URL, post_id)

                if full_post:
                    content = full_post
                    logging.info(f"Обрабатывается пост ID: {post_id}, title: {post_title}")
                    widgets = core.tripster_data_extractor.extract_tripster_widgets(content, TRIPSTER_DOMAIN)
                    deeplinks = core.tripster_data_extractor.extract_deeplinks(content, TRIPSTER_DOMAIN)

                    links_data = {
                        'post_id': post_id,
                        'post_title': post_title,
                        'widgets': widgets,
                        'deeplinks': deeplinks
                    }
                    all_links_data.append(links_data)

                else:
                    logging.warning(f"Не удалось получить данные поста с ID {post_id}.")
            except Exception as e:
                logging.error(f"Ошибка при обработке поста {post_id}: {e}")

        else:
            logging.warning("Ошибка: Не найден ID поста.")

    tripster_links_file = core.wp_api_utils.construct_json_file_path(core.wp_api_utils.TRIPSTER_LINKS_FILE)

    try:
        core.wp_api_utils.save_data_to_json_file(all_links_data, tripster_links_file)
        logging.info(f"Данные успешно сохранены в файл: {tripster_links_file}")
    except Exception as e:
        logging.error(f"Ошибка при сохранении данных в файл {tripster_links_file}: {e}")


def main():
    """Главная функция, запускает обработку ссылок Tripster."""
    process_tripster_links()


if __name__ == "__main__":
    process_tripster_links()