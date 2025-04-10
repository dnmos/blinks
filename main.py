import subprocess
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    """Запускает скрипты wordpress_post_indexer.py и tripster_link_processor.py последовательно."""
    try:
        logging.info("Запуск wordpress_post_indexer.py...")
        subprocess.run(["python", "-m", "scripts.wordpress_post_indexer"], check=True)
        logging.info("wordpress_post_indexer.py успешно завершен.")

        logging.info("Запуск tripster_link_processor.py...")
        subprocess.run(["python", "-m", "scripts.tripster_link_processor"], check=True)
        logging.info("tripster_link_processor.py успешно завершен.")

    except subprocess.CalledProcessError as e:
        logging.error(f"Ошибка при выполнении скрипта: {e}")
    except Exception as e:
        logging.error(f"Непредвиденная ошибка: {e}")

if __name__ == "__main__":
    main()