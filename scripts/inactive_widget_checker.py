import os
import json
from dotenv import load_dotenv
from core.wp_api_utils import construct_json_file_path
import asyncio
from core.telegram_notifier import send_telegram_message # Изменено

load_dotenv()

TRIPSTER_LINKS_FILE = os.getenv("TRIPSTER_LINKS_FILE", "tripster_links.json")


async def check_inactive_widgets():
    """
    Проверяет файл tripster_links.json на наличие неактивных виджетов и
    отправляет уведомление в Telegram со списком уникальных постов и номерами неактивных виджетов.
    """
    try:
        tripster_links_file = construct_json_file_path(TRIPSTER_LINKS_FILE)
        with open(tripster_links_file, 'r', encoding='utf-8') as f:
            links_data = json.load(f)
    except FileNotFoundError:
        print(f"Ошибка: Файл {TRIPSTER_LINKS_FILE} не найден.")
        return

    inactive_posts = []
    for item in links_data:
        post_id = item.get('post_id')
        post_title = item.get('post_title')
        widgets = item.get('widgets', [])
        inactive_widget_numbers = []

        for widget in widgets:
            if widget.get('status') == 'inactive':
                widget_number = widget.get('widget_number', 'Неизвестно')
                inactive_widget_numbers.append(widget_number)

        if inactive_widget_numbers:
            # Check if the post is already in the list
            if not any(post['post_title'] == post_title for post in inactive_posts):
                inactive_posts.append({
                    'post_title': post_title,
                    'widget_numbers': inactive_widget_numbers
                })

    if inactive_posts:
        message = "Обнаружены неактивные виджеты:\n\n"
        for post in inactive_posts:
            widget_numbers_str = ", ".join(map(str, post['widget_numbers']))
            message += f"{post['post_title']} - Виджет: {widget_numbers_str}\n\n"
        message += "Пожалуйста, проверьте эти виджеты."
        success = await send_telegram_message(message) # Изменено
        if not success:
            print("Предупреждение: Не удалось отправить сообщение в Telegram.")
    else:
        print("Неактивные виджеты не найдены.")
        success = await send_telegram_message("Неактивные виджеты Tripster не найдены.") # Изменено
        if not success:
            print("Предупреждение: Не удалось отправить сообщение в Telegram.")


def main():
    asyncio.run(check_inactive_widgets())

if __name__ == "__main__":
    main()