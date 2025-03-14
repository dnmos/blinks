import asyncio
import os
from dotenv import load_dotenv
from telegram import Bot
from telegram.error import TelegramError

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")


async def send_telegram_message(message):
    """Отправляет сообщение в Telegram асинхронно."""
    if not BOT_TOKEN or not CHAT_ID:
        print("Ошибка: BOT_TOKEN или CHAT_ID не определены в .env")
        return False

    try:
        bot = Bot(token=BOT_TOKEN)
        await bot.send_message(chat_id=CHAT_ID, text=message)
        print("Сообщение отправлено в Telegram!")
        return True
    except TelegramError as e:
        print(f"Ошибка при отправке сообщения в Telegram: {e}")
        return False