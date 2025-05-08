import os
import sys
import logging
from pathlib import Path

# Добавляем корневую директорию в PYTHONPATH
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def check_database():
    """Проверка подключения к базе данных и наличия необходимых таблиц"""
    try:
        # Проверяем наличие файла базы данных
        db_path = Path("database/database.db")
        if not db_path.exists():
            logger.error(f"База данных не найдена по пути: {db_path.absolute()}")
            return False
        
        # Проверяем подключение к базе данных
        from src.db import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Проверяем наличие необходимых таблиц
        required_tables = [
            'disciplines',
            'lecture_topics',
            'practical_topics',
            'labor_functions',
            'similarity_results'
        ]
        
        for table in required_tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
            if not cursor.fetchone():
                logger.error(f"Таблица {table} не найдена в базе данных")
                return False
        
        # Проверяем наличие данных
        for table in required_tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            logger.info(f"Таблица {table}: {count} записей")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при проверке базы данных: {str(e)}")
        return False

if __name__ == "__main__":
    if check_database():
        logger.info("База данных в порядке")
    else:
        logger.error("Проблемы с базой данных")
        sys.exit(1) 