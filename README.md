# Blink: Мониторинг неработающих виджетов и ссылок Tripster

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## О проекте

**Blink** - это скрипт на Python, предназначенный для автоматического мониторинга виджетов и партнерских ссылок Tripster, размещенных на сайтах WordPress.  Скрипт помогает выявлять неработающие виджеты и ссылки, которые могут возникать из-за удаления экскурсий на Tripster или других изменений.  При обнаружении проблем, Blink отправляет уведомления в Telegram, позволяя оперативно реагировать и поддерживать актуальность контента на сайте.

**Основные возможности:**

*   **Автоматическое обнаружение виджетов Tripster на страницах WordPress.**
*   **Проверка статуса виджетов Tripster.**
*   **Проверка работоспособности партнерских ссылок Tripster.**
*   **Уведомления в Telegram о неактивных виджетах и неработающих ссылках.**

## Быстрый старт

Эти шаги помогут вам быстро запустить `Blink` для мониторинга ваших виджетов и ссылок Tripster.

**Предварительные шаги:**

1.  **Клонируйте репозиторий:**
    ```bash
    git clone https://github.com/dnmos/blinks.git
    cd blinks
    ```

2.  **Установите зависимости:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Настройте `.env` файл:**
    Скопируйте файл `.env_example` в `.env` и заполните необходимые переменные окружения.  Необходимые переменные для запуска:

    ```env
    PROJECT_ROOT = ""      # Корневая директория проекта (абсолютный путь, например: /home/user/blinks).
    BASE_URL = ""          # Доменное имя вашего сайта WordPress (например: your-site.com).
    API_PATH = "/wp-json/wp/v2/posts" # Путь к API WordPress для получения постов.
    POSTS_PER_PAGE = 10     # Количество постов WordPress, получаемых за один запрос к API.
    TRIPSTER_DOMAIN = "tripster.ru" # Домен Tripster, используется для фильтрации и проверки ссылок.
    JSON_DIR = "json"        # Директория для хранения JSON файлов с собранными данными.
    POST_DATA_FILE = "post_data.json" # Имя файла для сохранения данных о постах WordPress.
    TRIPSTER_LINKS_FILE = "tripster_links.json" # Имя файла для сохранения списка ссылок Tripster.
    BOT_TOKEN = ""           # Токен вашего Telegram-бота. Получите токен при создании бота в Telegram.
    CHAT_ID = ""            # ID вашего чата в Telegram.  Узнайте ID чата, куда бот должен отправлять уведомления.
    ```
    Заполните значения напротив каждой переменной в файле `.env`.  **Важно: Не удаляйте и не изменяйте названия переменных.**

**Порядок запуска скриптов:**

Для корректной работы `Blink` необходимо запустить скрипты в следующей последовательности:

1.  **`wordpress_post_indexer.py`**:  Запрашивает посты из WordPress API, получает post_id и title, сохраняет их в JSON (`json/post_data.json`).
    ```bash
    python -m scripts/wordpress_post_indexer.py
    ```

2.  **`tripster_link_processor.py`**:  Извлекает виджеты и партнерские ссылки Tripster из постов, сохраняет их в JSON (`json/tripster_links.json`).
    ```bash
    python -m scripts/tripster_link_processor.py
    ```

3.  **`inactive_widget_checker.py`**:  Проверяет неактивные виджеты Tripster, используя данные из JSON (`json/tripster_links.json`), отправляет уведомления Telegram.
    ```bash
    python -m scripts/inactive_widget_checker.py
    ```

## Структура проекта

Проект `Blink` организован в следующие директории и файлы:

```
blinks/
├── core/
│ ├── telegram_notifier.py
│ ├── tripster_data_extractor.py
│ └── wp_api_utils.py
├── json/
│ ├── post_data.json
│ └── tripster_links.json
├── scripts/
│ ├── inactive_widget_checker.py
│ ├── tripster_link_processor.py
│ └── wordpress_post_indexer.py
├── .env
├── project_structure.txt
├── README.md
└── requirements.txt
```

**Описание директорий и файлов:**

*   **`core/`**:  Директория, содержащая основные, переиспользуемые модули проекта.
    *   `telegram_notifier.py`:  Модуль, отвечающий за отправку уведомлений в Telegram.  Содержит логику взаимодействия с Telegram Bot API.
    *   `tripster_data_extractor.py`:  Модуль, предназначенный для извлечения данных, связанных с Tripster (виджеты, партнерские ссылки) из HTML-контента.
    *   `wp_api_utils.py`:  Модуль, содержащий утилитарные функции для работы с WordPress API, такие как запросы к API, обработка ответов, сохранение данных в JSON файлы.

*   **`json/`**:  Директория для хранения JSON-файлов с данными, собранными и обработанными скриптами.
    *   `post_data.json`:  Файл, в котором хранятся данные о постах WordPress (ID, заголовки), полученные скриптом `wordpress_post_indexer.py`.
    *   `tripster_links.json`:  Файл, в котором хранится список партнерских ссылок и информация о виджетах Tripster, найденных и обработанных скриптами.

*   **`scripts/`**:  Директория, содержащая исполняемые скрипты проекта.
    *   `inactive_widget_checker.py`:  Скрипт для проверки неактивных виджетов Tripster и отправки уведомлений в Telegram.  Использует данные из `json/tripster_links.json` и модуль `core/telegram_notifier.py`.
    *   `tripster_link_processor.py`:  Скрипт для обработки партнерских ссылок Tripster, проверки их статуса и обновления данных в `json/tripster_links.json`.  Использует данные из `json/tripster_links.json`.
    *   `wordpress_post_indexer.py`:  Скрипт для индексации постов WordPress, извлечения ID и заголовков постов. Сохраняет результаты в `post_data.json`.

*   **`.env`**:  Файл конфигурации, содержащий переменные окружения, необходимые для работы скриптов (токены, URL сайта и т.д.).  **Важно: Создайте этот файл на основе `.env_example` и заполните пустые значения.**

*   **`project_structure.txt`**:  Файл `project_structure.txt`, содержащий структуру проекта в текстовом виде. Создан командой:

    ```bash
    tree -a -I "env|.git|.env_example|__init__.py" . > project_structure.txt
    ```

*   **`requirements.txt`**:  Файл, содержащий список Python-библиотек, необходимых для работы проекта. Используется для установки зависимостей командой `pip install -r requirements.txt`.

## Запуск скриптов

В разделе "Быстрый старт" описан основной порядок запуска скриптов.  Вот более подробное описание каждого скрипта и процесса их работы.

1.  **`wordpress_post_indexer.py`**:

    *   **Назначение:**  Скрипт является первым шагом в процессе мониторинга.  Он подключается к WordPress API вашего сайта, собирает список всех постов, и извлекает из них необходимую информацию: ID постов, заголовки.  Главная цель - подготовить данные для дальнейшей обработки и поиска виджетов и ссылок Tripster.
    *   **Действия:**
        *   Читает переменные окружения из файла `.env`, включая `BASE_URL`, `API_PATH`, `POSTS_PER_PAGE`.
        *   Запрашивает WordPress API (`/wp-json/wp/v2/posts`) постранично, получая список постов.
        *   Для каждого поста извлекает ID и заголовок.
        *   Сохраняет полученные данные (ID и заголовки постов) в JSON файл `json/post_data.json`.  Файл перезаписывается при каждом запуске скрипта.
    *   **Запуск:**
        ```bash
        python -m scripts/wordpress_post_indexer.py
        ```
    *   **Результат:**  Создается или обновляется файл `json/post_data.json`, содержащий список постов WordPress с их ID и заголовками.  Этот файл используется скриптом `tripster_link_processor.py` на следующем шаге.

2.  **`tripster_link_processor.py`**:

    *   **Назначение:**  Скрипт является вторым шагом. Он обрабатывает данные о постах WordPress, собранные на первом шаге, и ищет в контенте каждого поста виджеты и партнерские ссылки Tripster.  Затем он проверяет работоспособность партнерских ссылок и сохраняет результаты.
    *   **Действия:**
        *   Читает переменные окружения из файла `.env`, включая `TRIPSTER_DOMAIN`.
        *   Читает данные о постах из JSON файла `json/post_data.json`, созданного скриптом `wordpress_post_indexer.py`.
        *   Для каждого поста:
            *   Запрашивает полную версию поста через WordPress API, получая HTML-контент.
            *   Используя модуль `tripster_data_extractor.py`, извлекает из HTML-контента виджеты и партнерские ссылки Tripster.
            *   Для каждой партнерской ссылки:
                *   Проверяет ее работоспособность, отправляя HEAD-запрос.
                *   Анализирует ответ, чтобы определить, ведет ли ссылка на страницу "Экскурсия не проводится". (В текущей версии, проверка работоспособности ссылок **не реализована**, только извлечение).
            *   Сохраняет информацию о посте, найденных виджетах (с их статусом) и партнерских ссылках в JSON файл `json/tripster_links.json`.  Данные добавляются к существующему файлу, не перезаписывая его.
    *   **Запуск:**
        ```bash
        python -m scripts/tripster_link_processor.py
        ```
    *   **Результат:**  Обновляется файл `json/tripster_links.json`, который теперь содержит информацию о постах WordPress, найденных в них виджетах Tripster (с текущим статусом) и партнерских ссылках.  Этот файл используется скриптом `inactive_widget_checker.py` на следующем шаге. **Важно: В текущей версии скрипт `tripster_link_processor.py`  только извлекает виджеты и ссылки, но не проверяет работоспособность ссылок.**

3.  **`inactive_widget_checker.py`**:

    *   **Назначение:**  Скрипт является третьим и заключительным шагом.  Он анализирует данные о виджетах Tripster, собранные на предыдущих шагах, и проверяет их текущий статус через API Tripster.  В случае обнаружения неактивных виджетов, скрипт отправляет уведомление в Telegram.
    *   **Действия:**
        *   Читает переменные окружения из файла `.env`, включая `BOT_TOKEN`, `CHAT_ID`.
        *   Читает данные о виджетах из JSON файла `json/tripster_links.json`, созданного скриптом `tripster_link_processor.py`.
        *   Для каждого виджета в файле:
            *   Проверяет его статус, используя API Tripster (`https://experience.tripster.ru/api/widgets/widget/{widget_id}`). (В **текущей версии, проверка статуса виджетов не реализована**, только анализ данных из HTML).
            *   Определяет, является ли виджет неактивным (статус "inactive" на основе данных из HTML).
            *   Формирует сообщение для Telegram, содержащее список постов с неактивными виджетами и номера этих виджетов.
            *   Отправляет уведомление в Telegram, используя модуль `telegram_notifier.py`.
    *   **Запуск:**
        ```bash
        python -m scripts/inactive_widget_checker.py
        ```
    *   **Результат:**  В случае обнаружения неактивных виджетов, в Telegram отправляется уведомление.  В консоль выводится информация о процессе проверки и найденных проблемах.  **Важно: В текущей версии скрипт `inactive_widget_checker.py`  анализирует статус виджетов на основе данных, извлеченных из HTML-кода страниц WordPress, а не через API Tripster. Проверка через API не реализована.**

**Важные замечания по текущей версии скриптов:**

*   **Проверка работоспособности партнерских ссылок не реализована.**  Скрипт `tripster_link_processor.py` только извлекает ссылки, но не проверяет, ведут ли они на страницу "Экскурсия не проводится".  Эта функциональность может быть добавлена в будущих версиях.

## Лицензия

Проект `Blink` распространяется под лицензией [MIT License](https://opensource.org/licenses/MIT).

## Автор

Дмитрий Лузин