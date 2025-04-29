import pymysql
import logging
import traceback
import os
from dotenv import load_dotenv

load_dotenv()

# Настройка логирования
DEFAULT_LOG_LEVEL = logging.INFO
logging.basicConfig(level=DEFAULT_LOG_LEVEL, format='%(asctime)s - %(levelname)s - %(message)s')


def parse_sql(filename):
    """
    Парсит SQL-файл и возвращает список SQL-запросов.

    Args:
        filename (str): Имя SQL-файла.

    Returns:
        list: Список SQL-запросов.
    """
    queries = []
    DELIMITER = ";"
    query = ""

    try:
        with open(filename, "r") as file:
            data = file.readlines()

        for line in data:
            if not line.strip():
                continue

            if line.startswith("--"):
                continue

            if DELIMITER not in line:
                query += line.replace(DELIMITER, ";")
                query.strip()
                continue

            if query:
                query += line
                queries.append(query.strip())
                query = ""
            else:
                queries.append(line.strip())
        return queries
    except FileNotFoundError as e:
        logging.error(f"Файл {filename} не найден: {e}")
        return []
    except Exception as e:
        logging.error(f"Ошибка при парсинге SQL файла {filename}: {e}")
        return []


def connect():
    """
    Устанавливает соединение с базой данных MySQL.

    Returns:
        pymysql.Connection: Объект соединения с базой данных, или None в случае ошибки.
    """
    try:
        db_config = {
            'host': os.getenv("DB_HOST"),
            'user': os.getenv("DB_USER"),
            'database': os.getenv("DB_NAME"),
            'password': os.getenv("DB_PASSWORD"),
            'cursorclass': pymysql.cursors.DictCursor,
            'use_unicode': True,
            'charset': "utf8",
            'autocommit': True
        }
        connection = pymysql.connect(**db_config)

        logging.info("Успешное подключение к БД.")
        return connection
    except Exception as e:
        logging.error(f"Ошибка при подключении к БД: {e}")
        logging.error(traceback.format_exc())
        return None


def execute_sql_file(connection, filename):
    """
    Выполняет SQL-запросы из файла.

    Args:
        connection (pymysql.Connection): Объект соединения с базой данных.
        filename (str): Имя SQL-файла.
    """
    try:
        queries = parse_sql(filename)
        with connection.cursor() as cursor:
            for query in queries:
                cursor.execute(query)
                logging.info("Query is executed")
            connection.commit()
    except Exception as e:
        logging.error(f"Ошибка при выполнении SQL-запросов из файла {filename}: {e}")
        logging.error(traceback.format_exc())


def create():
    """Создает таблицы в базе данных."""
    connection = connect()
    if connection is None:
        logging.error("Не удалось установить соединение с БД, выход из create().")
        return

    create_tables_query_path = os.getenv("CREATE_TABLES_QUERY_PATH")
    if not create_tables_query_path:
        logging.error("Не задан CREATE_TABLES_QUERY_PATH в .env")
        return

    execute_sql_file(connection, create_tables_query_path)

    if connection:
        connection.close()
        logging.info("Соединение с БД закрыто.")


def drop():
    """Удаляет таблицы из базы данных."""
    connection = connect()
    if connection is None:
        logging.error("Не удалось установить соединение с БД, выход из drop().")
        return

    drop_tables_query_path = os.getenv("DROP_TABLES_QUERY_PATH")
    if not drop_tables_query_path:
        logging.error("Не задан DROP_TABLES_QUERY_PATH в .env")
        return

    execute_sql_file(connection, drop_tables_query_path)

    if connection:
        connection.close()
        logging.info("Соединение с БД закрыто.")


def insert_or_update_data(data):
    """Insert or update data in db."""
    connection = None
    try:
        connection = connect()
        if connection is None:
            logging.error("Не удалось установить соединение с БД, выход.")
            return

        with connection.cursor() as cursor:
            sql = """
                    INSERT INTO `wptq_tripster_links` (
                    `post_id`,
                    `post_title`,
                    `link_type`,
                    `exp_id`,
                    `exp_title`,
                    `exp_url`,
                    `link_status`,
                    `inactivity_reason`,
                    `is_unknown_type`
                    ) VALUES (%(post_id)s, %(post_title)s, %(link_type)s, %(exp_id)s, %(exp_title)s, %(exp_url)s, %(status)s, %(inactivity_reason)s, %(is_unknown_type)s)
                    ON DUPLICATE KEY UPDATE
                    `post_title` = VALUES(`post_title`),
                    `exp_title` = VALUES(`exp_title`),
                    `link_status` = VALUES(`link_status`),
                    `inactivity_reason` = VALUES(`inactivity_reason`),
                    `is_unknown_type` = VALUES(`is_unknown_type`);
            """
            cursor.execute(sql, data)
            connection.commit()

    except pymysql.err.IntegrityError as e:
        logging.error(f"Ошибка IntegrityError: {e}")
        if connection:
            connection.rollback() # Откатываем транзакцию при ошибке
    except Exception as e:
        logging.error(f"Ошибка при вставке/обновлении данных: {e}")
        logging.error(traceback.format_exc())
        if connection:
            connection.rollback()
    finally:
        if connection:
            connection.close()
            logging.info("Соединение с БД закрыто.")


def analyze_database():
    """
    Analyzes the database to identify inactive Tripster widgets and deeplinks.

    Returns:
        list: A list of dictionaries, where each dictionary represents an inactive
              widget or deeplink with its details.
    """
    connection = None
    try:
        connection = connect()
        if connection is None:
            logging.error("Не удалось установить соединение с БД.")
            return []

        with connection.cursor() as cursor:
            sql = """
                SELECT 
                    id, post_id, post_title, link_type, exp_id, exp_title, exp_url, link_status, inactivity_reason
                FROM 
                    wptq_tripster_links
                WHERE 
                    link_status = 'inactive'
            """
            cursor.execute(sql)
            inactive_items = cursor.fetchall()
            logging.info(f"Найдено {len(inactive_items)} неактивных элементов.")
            return inactive_items
    except pymysql.MySQLError as e:
        logging.error(f"Ошибка при анализе базы данных: {e}")
        logging.error(traceback.format_exc())
        return []
    except Exception as e:
        logging.error(f"Непредвиденная ошибка при анализе базы данных: {e}")
        logging.error(traceback.format_exc())
        return []
    finally:
        if connection:
            connection.close()
            logging.info("Соединение с БД закрыто.")