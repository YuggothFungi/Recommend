import os
import sys
import pytest
import sqlite3
import tempfile
from src.db import get_db_connection
from src.schema import init_db
from pathlib import Path

# Добавляем корневую директорию проекта в PYTHONPATH
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

@pytest.fixture(scope="function")
def db_connection():
    """Фикстура для создания соединения с базой данных"""
    # Создаем временный файл для базы данных
    temp_db = tempfile.NamedTemporaryFile(delete=False)
    temp_db.close()
    
    # Создаем соединение с временной базой данных
    conn = sqlite3.connect(temp_db.name)
    conn.row_factory = sqlite3.Row
    
    # Инициализируем базу данных
    cursor = conn.cursor()
    
    # Создание таблицы тем
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS topics (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            nltk_normalized_title TEXT,
            nltk_normalized_description TEXT,
            rubert_vector BLOB
        )
    """)
    
    # Создание таблицы компетенций
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS competencies (
            id TEXT PRIMARY KEY,
            category TEXT NOT NULL,
            description TEXT,
            nltk_normalized_category TEXT,
            nltk_normalized_description TEXT,
            rubert_vector BLOB
        )
    """)
    
    # Создание таблицы связи тем и компетенций
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS topic_competency (
            topic_id INTEGER,
            competency_id TEXT,
            PRIMARY KEY (topic_id, competency_id),
            FOREIGN KEY (topic_id) REFERENCES topics(id),
            FOREIGN KEY (competency_id) REFERENCES competencies(id)
        )
    """)
    
    # Создание таблицы трудовых функций
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS labor_functions (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            nltk_normalized_name TEXT,
            rubert_vector BLOB
        )
    """)
    
    # Создание таблицы типов компонентов
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS component_types (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        )
    """)
    
    # Создание таблицы компонентов
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS labor_components (
            id INTEGER PRIMARY KEY,
            component_type_id INTEGER,
            description TEXT,
            nltk_normalized_description TEXT,
            rubert_vector BLOB,
            FOREIGN KEY (component_type_id) REFERENCES component_types(id)
        )
    """)
    
    # Создание таблицы связи трудовых функций и компонентов
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS labor_function_components (
            labor_function_id TEXT,
            component_id INTEGER,
            PRIMARY KEY (labor_function_id, component_id),
            FOREIGN KEY (labor_function_id) REFERENCES labor_functions(id),
            FOREIGN KEY (component_id) REFERENCES labor_components(id)
        )
    """)
    
    # Создание таблицы векторов тем
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS topic_vectors (
            topic_id INTEGER PRIMARY KEY,
            tfidf_vector BLOB,
            rubert_vector BLOB,
            FOREIGN KEY (topic_id) REFERENCES topics(id)
        )
    """)
    
    # Создание таблицы векторов трудовых функций
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS labor_function_vectors (
            labor_function_id TEXT PRIMARY KEY,
            tfidf_vector BLOB,
            rubert_vector BLOB,
            FOREIGN KEY (labor_function_id) REFERENCES labor_functions(id)
        )
    """)
    
    # Создание таблицы связи тем и трудовых функций
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS topic_labor_function (
            topic_id INTEGER,
            labor_function_id TEXT,
            tfidf_similarity REAL,
            rubert_similarity REAL,
            PRIMARY KEY (topic_id, labor_function_id),
            FOREIGN KEY (topic_id) REFERENCES topics(id),
            FOREIGN KEY (labor_function_id) REFERENCES labor_functions(id)
        )
    """)
    
    # Заполнение справочника типов компонентов
    cursor.execute("""
        INSERT OR IGNORE INTO component_types (id, name) VALUES
        (1, 'action'),
        (2, 'skill'),
        (3, 'knowledge')
    """)
    
    conn.commit()
    
    yield conn
    
    # Закрываем соединение и удаляем временный файл
    conn.close()
    os.unlink(temp_db.name) 