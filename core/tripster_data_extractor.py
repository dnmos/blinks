import requests
from bs4 import BeautifulSoup
import socket
import random
import time
import re
from urllib.parse import urlparse, parse_qs
from core.tripster_api_utils import check_deeplink_status_api
import logging

# Настройка базовой конфигурации логирования
logging.basicConfig(
    level=logging.INFO,  # Уровень логирования (можно менять через переменные окружения)
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Константы
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
PAGE_EXPERIENCE_CLASS = 'page-experience'
PAGE_EXPERIENCE_WRAP_CLASS = 'page-experience__wrap'
EXP_PAUSED_CLASS = 'exp-paused'
EXP_PAUSED_PREVIEW_NAME_CLASS = 'exp-paused__preview-name'
PRODUCT_HEADER_CLASS = 'product-header'
DESTINATION_CLASS = 'destination'
AUTHOR_PAGE_CLASS = 'author_page'
WELCOME_TOP_CLASS = 'welcome-top'
TRIPSTER_WIDGET_CLASS = 'tripster-widget'


def fetch_and_parse_page(url, max_retries=3, retry_delay=2):
    """
    Выполняет HTTP-запрос и парсит HTML-страницу, обрабатывая ошибки и повторные попытки.

    Args:
        url (str): URL страницы для запроса.
        max_retries (int): Максимальное количество повторных попыток.
        retry_delay (int): Задержка между попытками в секундах.

    Returns:
        BeautifulSoup object: Объект BeautifulSoup с распарсенным HTML, или None в случае ошибки.
    """
    for attempt in range(max_retries):
        try:
            pause_time = random.uniform(1, 3)  # Пауза от 1 до 3 секунд
            logging.info(f"    Пауза перед запросом: {pause_time:.2f} секунд")
            time.sleep(pause_time)

            headers = {'User-Agent': USER_AGENT}
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            return BeautifulSoup(response.content, 'html.parser')

        except requests.exceptions.RequestException as e:
            # Обработка ошибок, связанных с DNS
            if isinstance(e.args[0], requests.exceptions.ConnectionError) and isinstance(e.args[0].args[1], socket.gaierror):
                error_message = f"Ошибка при запросе URL: Не удалось разрешить доменное имя (попытка {attempt + 1}/{max_retries})"
                logging.error(f"    {error_message}")
                time.sleep(retry_delay)  # Ждем перед следующей попыткой
                continue  # Переходим к следующей итерации цикла

            # Другие ошибки RequestException
            error_message = f"Ошибка при запросе URL: {e}"
            logging.error(f"    {error_message}")
            return None  # Возвращаем None в случае ошибки

        except Exception as e:
            error_message = f"Ошибка при обработке URL: {e}"
            logging.error(f"    {error_message}")
            return None  # Возвращаем None в случае ошибки

    return None  # Если все попытки неудачны


def is_experience_page(soup):
    """Проверяет, является ли страница страницей экскурсии."""
    return soup.find('div', class_=PAGE_EXPERIENCE_CLASS) is not None


def is_listing_page(soup):
    """Проверяет, является ли страница страницей списка экскурсий, авторской страницей или главной страницей и возвращает тип страницы и заголовок."""

    def extract_title(element):
        """Извлекает заголовок h1 из элемента, если он существует."""
        if element:
            title_element = element.find('h1')
            if title_element:
                return title_element.text.strip()
        return None

    product_header = soup.find('div', class_=PRODUCT_HEADER_CLASS)
    if product_header:
        title = extract_title(product_header)
        return "Список экскурсий", title if title else None

    destination = soup.find('div', class_=DESTINATION_CLASS)
    if destination:
         title = extract_title(destination)
         return "Список экскурсий",  title if title else None

    author_page = soup.find('div', class_=AUTHOR_PAGE_CLASS)
    if author_page:
        title = extract_title(author_page)
        return "Авторская страница",  title if title else None

    welcome_top = soup.find('div', class_=WELCOME_TOP_CLASS)
    if welcome_top:
        title = extract_title(welcome_top)
        return "Главная страница",  title if title else None

    return None, None


def extract_experience_info(soup):
    """Извлекает информацию (заголовок и причину) со страницы неактивной экскурсии."""
    page_experience_wrap = soup.find('div', class_=PAGE_EXPERIENCE_WRAP_CLASS)
    if page_experience_wrap and page_experience_wrap.get('style') == 'display:none;':
        logging.info(f"    Экскурсия не проводится: Element {PAGE_EXPERIENCE_WRAP_CLASS} найден и имеет style=\"display:none;\".")
        exp_paused = soup.find('div', class_=EXP_PAUSED_CLASS)
        if exp_paused:
            reason_paragraph = exp_paused.find('p')
            reason = reason_paragraph.text.strip() if reason_paragraph else "Причина не указана"
            title_element = exp_paused.find('h3', class_=EXP_PAUSED_PREVIEW_NAME_CLASS)
            title = title_element.text.strip() if title_element else "Заголовок не найден"
            logging.info(f"    Причина: {reason}")
            return title, reason
        else:
            logging.warning("    Причина не указана.")
            return "Заголовок не найден", "Причина не указана"
    else:
        logging.info(f"    Экскурсия активна: Element {PAGE_EXPERIENCE_WRAP_CLASS} не найден или style != \"display:none;\".")
        return None, None


def extract_widget_info(url, max_retries=3, retry_delay=2):
    """
    Извлекает информацию о неактивном виджете: заголовок и причину неактивности.
    """
    try:
        soup = fetch_and_parse_page(url, max_retries=3, retry_delay=2)

        if not soup:
            return None, "Не удалось получить данные страницы", False

        if is_experience_page(soup):
            title, reason = extract_experience_info(soup)
            if title and reason:
                return title, reason, False
            else:
                return None, None, False
        elif is_listing_page(soup):
            logging.info("    Страница со списком экскурсий, авторская страница или главная страница: Активна")
            return None, None, False
        else:
            logging.warning("    Неизвестный тип страницы: Требуется ручная проверка.")
            return None, "Требуется ручная проверка (неизвестный тип страницы)", True
    except Exception as e:
        logging.error(f"Ошибка при обработке URL: {url}. Ошибка: {e}")
        return None, f"Ошибка при обработке: {e}", True


def extract_deeplink_id(url):
    """Извлекает ID диплинка из URL."""
    try:
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        if 'u' in query_params:
            final_url = query_params['u'][0]
            match = re.search(r'/experience/(\d+)/?', final_url)
            if match:
                return int(match.group(1))
        else:
            match = re.search(r'/experience/(\d+)/?', url)
            if match:
                return int(match.group(1))
        return None
    except Exception as e:
        logging.error(f"Ошибка при извлечении deeplink_id из URL: {url}. Ошибка: {e}")
        return None


def extract_tripster_widgets(html_content, tripster_domain="tripster.ru", max_retries=3, retry_delay=2):
    """
    Извлекает виджеты Tripster из HTML-контента.
    """
    widgets = []
    soup = BeautifulSoup(html_content, 'html.parser')
    widget_divs = soup.find_all('div', class_=TRIPSTER_WIDGET_CLASS)

    for widget_div in widget_divs:
        try:
            # Извлекаем ID из data-experience-id
            widget_id = widget_div.get('data-experience-id')
            widget_href = widget_div.get('data-experience-href')

            # Инициализируем url значением None
            url = None
            title = None
            inactivity_reason = None
            is_unknown_type = False
            status = "active" #  По умолчанию считаем активным, пока не узнаем обратное

            # Формируем URL и получаем информацию о виджете
            widget_url = widget_href if widget_id else None
            if widget_url:
                print(f"  URL виджета: {widget_url}")  # Выводим URL в консоль
                title, inactivity_reason, is_unknown_type = extract_widget_info(widget_url, max_retries, retry_delay)
                url = widget_url #  Сохраняем widget_url
                if title is None and inactivity_reason is None:
                    status = "active" #  Активен
                    title_element = widget_div.find('a', class_='expcard__title expcard__title__link')
                    title = title_element.text.strip() if title_element else "Заголовок не найден"
                else:
                    status = "inactive" #  Не активен
            else:
                status = "inactive"
                title = "URL виджета не найден"
                inactivity_reason = "URL виджета не найден"
                is_unknown_type = True
                url = None

            widgets.append({
                'widget_number': len(widgets) + 1,  # нумерация виджетов
                'id': int(widget_id) if widget_id else None,  # Преобразуем в int, если widget_id есть, иначе None
                'status': status,
                'title': title,
                'url': url if url else None,
                'inactivity_reason': inactivity_reason,
                'is_unknown_type': is_unknown_type
            })
        except Exception as e:
            print(f"Ошибка при обработке виджета: {e}")

    return widgets


def extract_deeplinks(html_content, tripster_domain="tripster.ru"):
    """Извлекает диплинки Tripster из HTML-контента, исключая ссылки внутри виджетов."""
    deeplinks = []
    seen_links = set()
    soup = BeautifulSoup(html_content, 'html.parser')
    links = soup.find_all('a', href=True)

    for link in links:
        href = link['href']

        if tripster_domain in href:
            if link.find_parent('div', class_='tripster-widget'):
                continue

            deeplink_id = extract_deeplink_id(href)
            is_experience_link = deeplink_id is not None  # Проверяем, ведет ли ссылка на страницу экскурсии

            try:
                if deeplink_id:
                    # Если есть ID, сначала получаем данные из API
                    is_active, reason, title = check_deeplink_status_api(deeplink_id)
                    is_unknown = False

                    if is_experience_link and not is_active:
                        # Если это ссылка на страницу экскурсии и она не активна,
                        # пытаемся получить причину неактивности со страницы
                        page_soup = fetch_and_parse_page(href)
                        if page_soup:
                            title, page_reason = extract_experience_info(page_soup)
                            reason = page_reason  # Заменяем причину из API на причину со страницы
                else:
                    # Если ID извлечь не удалось
                    page_soup = fetch_and_parse_page(href)
                    if page_soup:
                        page_type, page_title = is_listing_page(page_soup)
                        if page_type:
                            is_active = True
                            title = page_title if page_title else page_type  #  Используем конкретный тип страницы или заголовок
                            reason = None
                            is_unknown = True
                        else:
                            is_active = False
                            title = "Без названия"
                            reason = "Не удалось извлечь ID экскурсии"
                            is_unknown = True
                    else:
                        is_active = False
                        title = "Не удалось получить данные страницы"
                        reason = "Не удалось получить данные страницы"
                        is_unknown = True

                anchor = link.text.strip()
                if not anchor:
                    anchor = link.get_text(strip=True) or "Без названия"  # Упрощенная логика

                link_tuple = (href, anchor)

                if link_tuple not in seen_links:
                    deeplinks.append({
                        'id': deeplink_id,
                        'anchor': anchor,
                        'url': href,
                        'status': 'active' if is_active else 'inactive',
                        'title': title,
                        'inactivity_reason': reason,
                        'is_unknown_type': is_unknown
                    })
                    seen_links.add(link_tuple)

            except Exception as e:
                print(f"Ошибка при обработке диплинка: {e}")

    return deeplinks