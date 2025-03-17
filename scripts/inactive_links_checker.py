import json
import os
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import asyncio
from core.telegram_notifier import send_telegram_message
import time
import random
from datetime import datetime
import socket  # Для обработки ошибок DNS

# Предполагаем, что core определен в другом файле и импортирован
# from . import core  # Раскомментируйте, если 'core' находится в том же пакете
import core.wp_api_utils  # Измените путь, если структура проекта другая

load_dotenv()

TRIPSTER_LINKS_FILE = os.getenv("TRIPSTER_LINKS_FILE", "tripster_links.json")
BASE_URL = os.getenv("BASE_URL", "travelq.ru")  # Добавлено получение BASE_URL из .env

MAX_RETRIES = 3  # Максимальное количество повторных попыток
RETRY_DELAY = 2  # Задержка между попытками в секундах


async def check_inactive_links():
    """
    Проверяет deeplink'и в tripster_links.json, определяет неактивные, указывает причины и отправляет отчет в Telegram.
    """
    tripster_links_file = core.wp_api_utils.construct_json_file_path(TRIPSTER_LINKS_FILE)

    try:
        with open(tripster_links_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"JSON файл '{tripster_links_file}' успешно загружен.")
    except FileNotFoundError:
        print(f"Файл '{tripster_links_file}' не найден.")
        return
    except json.JSONDecodeError:
        print(f"Ошибка декодирования JSON в файле '{tripster_links_file}'. Возможно, файл поврежден или имеет неверный формат.")
        return

    num_posts_to_check = len(data)  # Проверяем все посты
    total_inactive_links = 0
    total_unknown_type_links = 0  # Счетчик ссылок с неизвестным типом
    inactive_posts = []

    start_time = time.time()  # Засекаем время начала

    for i, post in enumerate(data):  # Итерируемся по всем постам
        post_title = post.get('post_title', 'Без названия')
        print(f"Обработка поста {i + 1}: {post_title}")
        inactive_links = []
        deeplinks = post.get('deeplinks', [])

        for link_number, deeplink in enumerate(deeplinks, start=1):
            anchor = deeplink.get('anchor', 'Без анкора')
            url = deeplink.get('url')
            print(f"  Проверка deeplink {link_number}: {anchor}")

            # Повторные попытки выполнения запроса
            is_inactive = False
            inactivity_reason = "Не удалось определить причину"  # Инициализация
            is_unknown_type = False  # Инициализация

            for attempt in range(MAX_RETRIES):
                try:
                    # Пауза перед запросом (имитация поведения человека)
                    pause_time = random.uniform(1, 3)  # Пауза от 1 до 3 секунд
                    print(f"    Пауза перед запросом: {pause_time:.2f} секунд")
                    time.sleep(pause_time)

                    # Запрос с User-Agent
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                    }
                    response = requests.get(url, headers=headers)
                    response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
                    soup = BeautifulSoup(response.content, 'html.parser')

                    # 1. Проверяем, является ли страница страницей экскурсии
                    page_experience = soup.find('div', class_='page-experience')

                    if page_experience:
                        # Это страница экскурсии
                        page_experience_wrap = soup.find('div', class_='page-experience__wrap')
                        if page_experience_wrap and page_experience_wrap.get('style') == 'display:none;':
                            print(f"    Экскурсия не проводится: Element page-experience__wrap найден и имеет style=\"display:none;\".")
                            # Проверяем наличие exp-paused и причину
                            exp_paused = soup.find('div', class_='exp-paused')
                            if exp_paused:
                                reason_paragraph = exp_paused.find('p')
                                reason = reason_paragraph.text.strip() if reason_paragraph else "Причина не указана"
                                print(f"    Причина: {reason}")
                                is_inactive = True
                                inactivity_reason = reason
                            else:
                                print("    Причина не указана.")
                                is_inactive = True
                                inactivity_reason = "Причина не указана"

                        else:
                            print("    Экскурсия активна: Element page-experience__wrap не найден или style != \"display:none;\".")

                    else:
                        # 2. Если это не страница экскурсии, проверяем, является ли это страница списка экскурсий, авторская страница или главная страница
                        product_header = soup.find('div', class_='product-header')
                        destination = soup.find('div', class_='destination')  # Добавлено: Ищем class="destination"
                        author_page = soup.find('div', class_='author_page')  # Добавлено: Ищем class="author_page"
                        welcome_top = soup.find('div', class_='welcome-top')  # Добавлено: Ищем class="welcome-top"

                        if product_header or destination or author_page or welcome_top:  # Проверяем все четыре класса
                            print("    Страница со списком экскурсий, авторская страница или главная страница: Активна")
                        else:
                            print("    Неизвестный тип страницы: Требуется ручная проверка.")
                            is_inactive = True
                            is_unknown_type = True  # Добавлено: Устанавливаем флаг
                            inactivity_reason = "Требуется ручная проверка (неизвестный тип страницы)"
                            total_unknown_type_links += 1  # Увеличиваем счетчик
                    break  # Если запрос успешен, выходим из цикла повторных попыток

                except requests.exceptions.RequestException as e:
                    # Обработка ошибок, связанных с DNS
                    if isinstance(e.args[0], requests.exceptions.ConnectionError) and isinstance(e.args[0].args[1], socket.gaierror):
                        inactivity_reason = f"Ошибка при запросе URL: Не удалось разрешить доменное имя (попытка {attempt + 1}/{MAX_RETRIES})"
                        print(f"    {inactivity_reason}")
                        time.sleep(RETRY_DELAY)  # Ждем перед следующей попыткой
                        is_inactive = True # Считаем неактивной при ошибке DNS
                    else:
                        # Другие ошибки RequestException
                        inactivity_reason = f"Ошибка при запросе URL: {e}"
                        print(f"    {inactivity_reason}")
                        is_inactive = True # Считаем неактивной при любой ошибке RequestException
                        break  # Выходим из цикла повторных попыток

                except Exception as e:
                    inactivity_reason = f"Ошибка при обработке URL: {e}"
                    print(f"    {inactivity_reason}")
                    is_inactive = True # Считаем неактивной при любой другой ошибке
                    break  # Выходим из цикла повторных попыток
            
            if is_inactive:
                inactive_links.append({
                    'link_number': link_number,
                    'reason': inactivity_reason,
                    'is_unknown_type': is_unknown_type  # Добавлено: Сохраняем флаг
                })
                total_inactive_links += 1

        if inactive_links:
            inactive_posts.append({
                'post_title': post_title,
                'links': inactive_links
            })

    end_time = time.time()  # Засекаем время окончания
    duration = end_time - start_time  # Вычисляем продолжительность

    # Формируем отчет
    report_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = f"Отчет от {report_date}\n"
    message += f"Сайт: {BASE_URL}\n"  # Используем BASE_URL из .env
    message += f"Проверено постов: {num_posts_to_check}\n"
    message += f"Найдено неактивных ссылок: {total_inactive_links}\n"
    message += f"Найдено ссылок с неизвестным типом: {total_unknown_type_links}\n"  # Добавлено
    message += f"Продолжительность проверки: {duration:.2f} секунд\n\n"

    if inactive_posts:
        message += "Обнаружены неактивные deeplink'и:\n\n"
        for post in inactive_posts:
            post_title = post['post_title']
            message += f"{post_title}:\n"
            for link in post['links']:
                link_number = link['link_number']
                reason = link['reason']
                # Добавлено: Помечаем ссылки с неизвестным типом
                if link['is_unknown_type']:
                    message += f"  {link_number}. [Неизвестный тип] Причина: {reason}\n"
                else:
                    message += f"  {link_number}. Причина: {reason}\n"
            message += "\n"
        message += "Пожалуйста, проверьте эти deeplink'и."
    else:
        message += "Неактивные deeplink'и не найдены."

    success = await send_telegram_message(message)
    if not success:
        print("Предупреждение: Не удалось отправить сообщение в Telegram.")


def main():
    asyncio.run(check_inactive_links())


if __name__ == "__main__":
    main()