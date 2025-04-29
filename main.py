import subprocess
import logging
import os
import sys
import asyncio

# Добавляем путь к корневой директории проекта
PROJECT_ROOT = os.getenv("PROJECT_ROOT")
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from db import db  # Импортируем модуль db
from report import report_generator # Импортируем модуль report_generator
from notifications import telegram_notifier # Import the telegram_notifier

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def main():
    """Запускает скрипты wordpress_post_indexer.py и tripster_link_processor.py последовательно."""
    try:
        logging.info("Запуск wordpress_post_indexer.py...")
        subprocess.run(["python", "-m", "scripts.wordpress_post_indexer"], check=True)
        logging.info("wordpress_post_indexer.py успешно завершен.")

        logging.info("Запуск tripster_link_processor.py...")
        subprocess.run(["python", "-m", "scripts.tripster_link_processor"], check=True)
        logging.info("tripster_link_processor.py успешно завершен.")

        # Вызываем функцию analyze_database() после tripster_link_processor.py
        logging.info("Анализ данных в базе данных...")
        inactive_items = db.analyze_database()
        logging.info("Анализ данных в базе данных завершен.")

        if inactive_items:
            logging.info(f"Найдено {len(inactive_items)} неактивных элементов.")
            # Генерируем отчет
            logging.info("Генерация отчета...")
            report_path = report_generator.generate_report(inactive_items)
            logging.info("Отчет успешно сгенерирован.")

             # Send Telegram notification
            if report_path:
                logging.info("Отправка уведомления в Telegram...")
                await telegram_notifier.send_telegram_notification(report_path)
                logging.info("Уведомление в Telegram успешно отправлено.")
            else:
                logging.error("Не удалось сгенерировать отчет, уведомление в Telegram не отправлено.")
        else:
            logging.info("Неактивные элементы не найдены.")

    except subprocess.CalledProcessError as e:
        logging.error(f"Ошибка при выполнении скрипта: {e}")
    except Exception as e:
        logging.error(f"Непредвиденная ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(main())