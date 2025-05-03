import sqlite3
import os

def get_db_connection():
    """Получение соединения с базой данных"""
    # Создаем директорию для базы данных, если она не существует
    db_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database')
    os.makedirs(db_dir, exist_ok=True)
    
    # Подключаемся к базе данных
    db_path = os.path.join(db_dir, 'database.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

# Здесь будут функции для работы с базой данных 