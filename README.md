# Tripster Widget Checker

## Описание

Этот проект предназначен для автоматической проверки наличия и активности виджетов Tripster на сайте WordPress.  Он состоит из нескольких скриптов, которые взаимодействуют с API WordPress, извлекают данные о виджетах и диплинках, анализируют их и отправляют уведомления в Telegram о найденных проблемах (например, о неактивных виджетах).

## Функциональность

Проект выполняет следующие задачи:

*   **Получение данных о постах из WordPress API:** Загружает список всех постов с сайта WordPress через API.
*   **Извлечение виджетов и диплинков:** Анализирует содержимое каждого поста, извлекая информацию о виджетах Tripster (заголовок, URL, статус) и диплинках.
*   **Декодирование HTML-сущностей:** Автоматически декодирует HTML-сущности (например, `—`) в заголовках постов и виджетов, обеспечивая корректное отображение текста.
*   **Нумерация виджетов:**  Присваивает каждому виджету в посте порядковый номер, начиная с 1.
*   **Проверка активности виджетов:**  Определяет, какие виджеты неактивны (например, если экскурсия была удалена на Tripster).
*   **Уведомления в Telegram:** Отправляет уведомления в Telegram о постах, содержащих неактивные виджеты, с указанием заголовка поста и номеров неактивных виджетов.

## Структура проекта

Проект состоит из следующих файлов:

*   **.env:** Файл, содержащий настройки проекта (URL сайта WordPress, API-ключи, токены Telegram и т.д.). **Важно:** Этот файл не должен попасть в систему контроля версий (например, Git).
*   **`wp_api_utils.py`:** Содержит функции для взаимодействия с WordPress API:
    *   `fetch_posts()`: Получение списка постов.
    *   `fetch_post_by_id()`: Получение данных поста по ID.
    *   `save_post_data_to_json()`: Сохранение данных о постах в JSON-файл.
    *   `save_tripster_links_to_json()`: Сохранение данных о виджетах и диплинках в JSON-файл.
*   **`data_processing.py`:** Содержит функции для обработки HTML-контента:
    *   `extract_tripster_widgets()`: Извлечение виджетов Tripster из HTML.
    *   `extract_deeplinks()`: Извлечение диплинков Tripster из HTML.
    *    `unescape_html()`: Декодирует HTML-сущности.
*   **`primary_processing.py`:** Скрипт, выполняющий первичную обработку:
    *   Получает список постов из WordPress API.
    *   Извлекает ID и заголовки постов.
    *   Сохраняет ID и заголовки в файл `post_data.json`.
*   **`secondary_processing.py`:** Скрипт, выполняющий вторичную обработку:
    *   Читает данные о постах из файла `post_data.json`.
    *   Для каждого поста получает его полный контент из WordPress API.
    *   Извлекает виджеты и диплинки из контента.
    *   Добавляет нумерацию к виджетам.
    *   Сохраняет информацию о виджетах и диплинках в файл `tripster_links.json`.
*   **`telegram_notifier.py`:** Содержит функции для отправки сообщений в Telegram:
    *   `send_telegram_message()`: Отправляет сообщение в Telegram с использованием `BOT_TOKEN` и `CHAT_ID` из `.env`. Использует `asyncio` для асинхронной отправки сообщений.
*   **`inactive_widget_checker.py`:** Скрипт для проверки неактивных виджетов и отправки уведомлений:
    *   Читает данные из `tripster_links.json`.
    *   Определяет посты, содержащие неактивные виджеты.
    *   Формирует сообщение в Telegram со списком таких постов и номерами виджетов.
    *   Отправляет сообщение в Telegram.
*   **`post_data.json`:**  Файл, содержащий ID и заголовки всех постов с сайта WordPress.  Создается скриптом `primary_processing.py`.
*   **`tripster_links.json`:**  Файл, содержащий информацию о виджетах и диплинках, найденных в каждом посте.  Создается скриптом `secondary_processing.py`.

## Требования

*   Python 3.7 или выше
*   Библиотеки:
    *   `requests`
    *   `beautifulsoup4`
    *   `python-dotenv`
    *   `python-telegram-bot`

Установите необходимые библиотеки с помощью pip:

```bash
pip install requests beautifulsoup4 python-dotenv python-telegram-bot
```

## Настройка

Клонируйте репозиторий с кодом проекта.

Создайте файл .env в корневой директории проекта и заполните его необходимыми переменными окружения (см. пример .env.example).

Отредактируйте файл .env, указав свои значения для:

* BASE_URL: URL вашего сайта WordPress (например, yourwebsite.com).
* API_PATH: Путь к API WordPress (по умолчанию /wp-json/wp/v2/posts).
* POSTS_PER_PAGE: Количество постов на одной странице API (по умолчанию 10).
* POST_DATA_FILE: Имя файла для хранения данных о постах (по умолчанию post_data.json).
* TRIPSTER_DOMAIN: Домен сайта Tripster (по умолчанию tripster.ru).
* TRIPSTER_LINKS_FILE: Имя файла для хранения данных о виджетах и диплинках (по умолчанию tripster_links.json).
* BOT_TOKEN: Токен вашего Telegram-бота (полученный от BotFather).
* CHAT_ID: ID чата Telegram, в который будут отправляться уведомления.

## Использование

Первоначальная обработка: Запустите скрипт primary_processing.py, чтобы получить список постов и сохранить их ID и заголовки в файл post_data.json:

```
python primary_processing.py
```

Вторичная обработка: Запустите скрипт secondary_processing.py, чтобы извлечь виджеты и диплинки из каждого поста и сохранить их в файл tripster_links.json:

```
python secondary_processing.py
```

Проверка неактивных виджетов: Запустите скрипт inactive_widget_checker.py, чтобы проверить наличие неактивных виджетов и отправить уведомление в Telegram:

```
python inactive_widget_checker.py
```

## Планирование

Чтобы автоматизировать проверку неактивных виджетов, можно настроить запуск скрипта inactive_widget_checker.py по расписанию с помощью cron (в Linux) или Task Scheduler (в Windows).

## Дополнительная информация

```
tree -a -I "env|_pycache_" . > project_structure.txt
```

Рекомендуется использовать виртуальное окружение Python (venv) для управления зависимостями проекта.

Не храните секретные ключи (например, BOT_TOKEN) непосредственно в коде. Используйте переменные окружения (файл .env) для хранения такой информации.

Учитывайте лимиты Telegram API при отправке сообщений, чтобы избежать блокировки бота.

Этот проект является примером и может быть адаптирован для других задач, связанных с анализом и мониторингом контента на сайтах WordPress.

Ключевые моменты:

*   **Охват всех тем:** Описание включает все этапы проекта, файлы, библиотеки, настройку и использование.
*   **Акцент на .env:** Особо подчеркнута важность файла `.env` и хранения секретных ключей.
*   **Инструкции по запуску:** Даны четкие инструкции по запуску каждого скрипта.
*   **Планирование:** Предложено использовать планировщик задач для автоматизации.

Чтобы улучшить этот `README.md`, можно добавить:

*   Скриншоты работы скриптов (если уместно).
*   Более подробные инструкции по настройке Telegram-бота.
*   Инструкции по установке cron или Task Scheduler.
*   Информацию о том, как можно расширить функциональность проекта (например, добавление других проверок или использование других источников данных).
