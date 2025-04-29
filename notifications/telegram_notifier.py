import os
import logging
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from telegram import Bot
from telegram.error import TelegramError

load_dotenv()

# Настройка логирования
DEFAULT_LOG_LEVEL = logging.INFO
logging.basicConfig(level=DEFAULT_LOG_LEVEL, format='%(asctime)s - %(levelname)s - %(message)s')

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")  # todo получить Chat ID
MAX_RETRIES = 3  # Maximum number of retries for sending the report


async def send_telegram_notification(report_path):
    """
    Sends a notification to a Telegram bot with the generated report.

    Args:
        report_path (str): The path to the generated PDF report.
    """
    try:
        if not TELEGRAM_BOT_TOKEN:
            logging.error("Отсутствует токен Telegram-бота. Пожалуйста, укажите TELEGRAM_BOT_TOKEN в файле .env.")
            return

        if not TELEGRAM_CHAT_ID:
            logging.error("Отсутствует Chat ID Telegram. Пожалуйста, укажите TELEGRAM_CHAT_ID в файле .env.")
            return

        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        chat_id = TELEGRAM_CHAT_ID

        # Prepare the message
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message_text = f"Проверка виджетов и ссылок Tripster завершена: {now}\nПолный отчет прилагается."

        # Send the message
        try:
            await bot.send_message(chat_id=chat_id, text=message_text)
            logging.info(f"Уведомление успешно отправлено в Telegram чат {chat_id}")
        except TelegramError as e:
            logging.error(f"Ошибка при отправке уведомления в Telegram: {e}")

        # Send the report document with retries
        for attempt in range(MAX_RETRIES):
            try:
                with open(report_path, 'rb') as document:
                    await bot.send_document(chat_id=chat_id, document=document, filename="tripster_report.pdf")
                logging.info(f"Отчет успешно отправлен в Telegram чат {chat_id} (попытка {attempt + 1})")
                break  # Отправка успешна, выходим из цикла
            except TelegramError as e:
                logging.error(f"Ошибка при отправке отчета в Telegram (попытка {attempt + 1}): {e}")
                if attempt == MAX_RETRIES - 1:
                    logging.error(f"Превышено максимальное количество попыток отправки отчета в Telegram.")
                await asyncio.sleep(5)  # Wait before retrying

    except Exception as e:
        logging.error(f"Ошибка при отправке уведомления в Telegram: {e}")