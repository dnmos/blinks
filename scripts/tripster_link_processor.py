import os
import json
from dotenv import load_dotenv
import core.wp_api_utils
import core.tripster_data_extractor
import core.telegram_notifier

load_dotenv()

TRIPSTER_DOMAIN = os.getenv("TRIPSTER_DOMAIN", "tripster.ru")

def process_tripster_links():
    """Извлекает и сохраняет виджеты и диплинки из постов WordPress."""
    try:
        post_data_file = core.wp_api_utils.construct_json_file_path(core.wp_api_utils.POST_DATA_FILE)

        with open(post_data_file, 'r', encoding='utf-8') as f:
            post_data = json.load(f)

    except FileNotFoundError:
        print(f"Ошибка: Файл {post_data_file} не найден.")
        return
    except json.JSONDecodeError:
        print(f"Ошибка: Некорректный JSON в файле {post_data_file}.")
        return
    except Exception as e:
        print(f"Непредвиденная ошибка при чтении файла: {e}")
        return

    if not post_data:
        print("Нет данных о постах для обработки.")
        return

    all_links_data = []

    for post in post_data:
        post_id = post.get('id')
        post_title = post.get('title')

        if post_id:
            full_post = core.wp_api_utils.fetch_wordpress_post_by_id(core.wp_api_utils.API_URL, post_id)

            if full_post:
                content = full_post
                print(f"Обрабатывается пост ID: {post_id}, title: {post_title}")
                widgets = core.tripster_data_extractor.extract_tripster_widgets(content, TRIPSTER_DOMAIN)
                deeplinks = core.tripster_data_extractor.extract_deeplinks(content, TRIPSTER_DOMAIN)

                for i, widget in enumerate(widgets):
                    widget['widget_number'] = i + 1

                links_data = {
                    'post_id': post_id,
                    'post_title': post_title,
                    'widgets': widgets,
                    'deeplinks': deeplinks
                }
                all_links_data.append(links_data)

            else:
                print(f"Не удалось получить данные поста с ID {post_id}.")
        else:
            print("Ошибка: Не найден ID первого поста.")

    tripster_links_file = core.wp_api_utils.construct_json_file_path(core.wp_api_utils.TRIPSTER_LINKS_FILE)

    core.wp_api_utils.append_data_to_json_file(all_links_data, tripster_links_file)


def main():
    """Главная функция, запускает обработку ссылок Tripster."""
    process_tripster_links()


if __name__ == "__main__":
        process_tripster_links()