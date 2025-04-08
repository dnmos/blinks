import requests
import json
from dotenv import load_dotenv
import os
import logging

# Настройка базовой конфигурации логирования
logging.basicConfig(
    level=logging.INFO,  # Уровень логирования (можно менять через переменные окружения)
    format='%(asctime)s - %(levelname)s - %(message)s'
)

load_dotenv()

BASE_URL = os.getenv("BASE_URL")
if BASE_URL and not BASE_URL.startswith("https://"):
    BASE_URL = "https://" + BASE_URL

API_PATH = os.getenv("API_PATH", "/wp-json/wp/v2/posts")
API_URL = BASE_URL + API_PATH
JSON_DIR = os.getenv("JSON_DIR", "json")
POST_DATA_FILE = os.getenv("POST_DATA_FILE", "post_data.json")
TRIPSTER_LINKS_FILE = os.getenv("TRIPSTER_LINKS_FILE", "tripster_links.json")


def fetch_wordpress_posts(api_url, page=1):
    """Получает список постов из WordPress API с учетом пагинации."""
    try:
        response = requests.get(f"{api_url}?page={page}")
        response.raise_for_status()
        total_pages = int(response.headers.get('X-WP-TotalPages', 1))
        return response.json(), total_pages
    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка при получении постов со страницы {page}: {e}")
        return [], 1


def fetch_wordpress_post_by_id(api_url, post_id):
    """Получает данные поста по его ID из API WordPress."""
    try:
        response = requests.get(f"{api_url}/{post_id}")
        response.raise_for_status()
        post = response.json()

        if post and 'content' in post and 'rendered' in post['content']:
            content = post['content']['rendered']
            # Явно декодируем контент в UTF-8
            try:
                content = content.encode('utf-8').decode('utf-8')
            except Exception as e:
                logging.error(f"Ошибка при декодировании контента в UTF-8 для поста с ID {post_id}: {e}")
                content = ""
            return content
        else:
            logging.warning(f"Предупреждение: Не удалось извлечь контент для поста с ID {post_id}")
            return ""  # Возвращаем пустую строку, чтобы избежать ошибок
    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка при получении поста с ID {post_id}: {e} url={api_url}/{post_id}")
        return ""  # Возвращаем пустую строку в случае ошибки
    except json.JSONDecodeError as e:
        logging.error(f"Ошибка при разборе JSON для поста с ID {post_id}: {e}")
        return ""
    except Exception as e:
        logging.error(f"Непредвиденная ошибка при получении или обработке поста с ID {post_id}: {e}")
        return ""

def construct_json_file_path(filename):
    """Строит полный путь к JSON-файлу, учитывая директорию JSON_DIR."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, '..'))
    return os.path.join(project_root, JSON_DIR, filename)


def save_data_to_json_file(data, filename=None):
    """Сохраняет данные в JSON-файл."""
    if filename is None:
        filename = construct_json_file_path(POST_DATA_FILE)
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logging.info(f"Данные успешно сохранены в файл: {filename}")
    except Exception as e:
        logging.error(f"Ошибка при сохранении данных в файл: {e}")