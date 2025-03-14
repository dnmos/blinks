from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET


def unescape_html(text):
    """Декодирует все HTML-сущности в строке."""
    return ET.XML(f'<t>{text}</t>').text


def extract_tripster_widgets(html_content, tripster_domain):
    """
    Извлекает виджеты Tripster из HTML-контента и возвращает список виджетов.
    Декодирует HTML-сущности в заголовках.
    Добавляет нумерацию виджетов, начиная с 1 для каждого поста.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    widgets = []
    for i, widget in enumerate(soup.find_all('div', class_='tripster-widget')):
        if 'tripster-message-off' in widget.get('class', []):
            widgets.append({'widget_number': i + 1, 'status': 'inactive', 'title': 'Экскурсия не найдена', 'url': None})
        else:
            figcaption = widget.find('figcaption', class_='expcard-info')
            if figcaption:
                a_tag = figcaption.find('a', class_='expcard__title expcard__title__link', href=True)
                if a_tag and tripster_domain in a_tag['href']:
                    title = a_tag.text.strip()
                    # Decode HTML entities using ET
                    decoded_title = unescape_html(title)
                    url = a_tag['href']
                    widgets.append({'widget_number': i + 1, 'status': 'active', 'title': decoded_title, 'url': url})
    return widgets


def extract_deeplinks(html_content, tripster_domain):
    """
    Извлекает диплинки Tripster из HTML-контента, исключая ссылки внутри виджетов.
    Декодирует HTML-сущности в anchor text.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    deeplinks = []
    excluded_classes = {
        'expcard__img-link',
        'expcard__title',
        'expcard__title__link',
        'expcard__text__link',
        'expcard__left_user',
        'rating',
        'expcard__review',
        'grey-button'
    }

    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        if tripster_domain in href:
            classes = set(a_tag.get('class', []))
            if not (classes & excluded_classes):
                anchor = a_tag.text.strip()
                # Decode HTML entities using ET
                decoded_anchor = unescape_html(anchor)
                deeplinks.append({'anchor': decoded_anchor, 'url': href})
    return deeplinks