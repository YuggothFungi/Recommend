import sqlite3
import os
from db import get_db_connection

def init_db():
    """Инициализация базы данных"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Создание таблицы тем
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS topics (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            nltk_normalized_title TEXT,
            nltk_normalized_description TEXT
        )
    """)
    
    # Создание таблицы компетенций
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS competencies (
            id TEXT PRIMARY KEY,
            category TEXT NOT NULL,
            description TEXT,
            nltk_normalized_category TEXT,
            nltk_normalized_description TEXT
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
            description TEXT,
            nltk_normalized_name TEXT,
            nltk_normalized_description TEXT
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
            vector BLOB NOT NULL,
            FOREIGN KEY (topic_id) REFERENCES topics(id)
        )
    """)
    
    # Создание таблицы векторов трудовых функций
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS labor_function_vectors (
            labor_function_id TEXT PRIMARY KEY,
            vector BLOB NOT NULL,
            FOREIGN KEY (labor_function_id) REFERENCES labor_functions(id)
        )
    """)
    
    # Создание таблицы связи тем и трудовых функций
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS topic_labor_function (
            topic_id INTEGER,
            labor_function_id TEXT,
            cosine_similarity_score REAL,
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
    conn.close()

def reset_db():
    """Сброс базы данных"""
    db_path = 'data/database.db'
    if os.path.exists(db_path):
        os.remove(db_path)
    init_db()

if __name__ == "__main__":
    reset_db() 