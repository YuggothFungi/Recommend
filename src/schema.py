import os
from src.db import get_db_connection

def init_db():
    """Инициализация базы данных"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Создание таблицы дисциплин
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS disciplines (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            competencies TEXT,
            goals TEXT,
            tasks TEXT,
            nltk_normalized_name TEXT,
            nltk_normalized_competencies TEXT,
            nltk_normalized_goals TEXT,
            nltk_normalized_tasks TEXT,
            rubert_vector BLOB
        )
    """)
    
    # Создание таблицы тем
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS topics (
            id INTEGER PRIMARY KEY,
            discipline_id INTEGER,
            title TEXT NOT NULL,
            description TEXT,
            hours INTEGER,
            nltk_normalized_title TEXT,
            nltk_normalized_description TEXT,
            rubert_vector BLOB,
            FOREIGN KEY (discipline_id) REFERENCES disciplines(id)
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
    return conn

def reset_db():
    """Сброс базы данных"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Удаление всех таблиц
    cursor.execute("DROP TABLE IF EXISTS topic_labor_function")
    cursor.execute("DROP TABLE IF EXISTS topic_competency")
    cursor.execute("DROP TABLE IF EXISTS labor_function_components")
    cursor.execute("DROP TABLE IF EXISTS topic_vectors")
    cursor.execute("DROP TABLE IF EXISTS labor_function_vectors")
    cursor.execute("DROP TABLE IF EXISTS topics")
    cursor.execute("DROP TABLE IF EXISTS disciplines")
    cursor.execute("DROP TABLE IF EXISTS competencies")
    cursor.execute("DROP TABLE IF EXISTS labor_functions")
    cursor.execute("DROP TABLE IF EXISTS labor_components")
    cursor.execute("DROP TABLE IF EXISTS component_types")
    
    conn.commit()
    return conn

def update_schema():
    """Обновление схемы базы данных"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Проверяем существование таблицы disciplines
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='disciplines'
    """)
    if not cursor.fetchone():
        # Создаем таблицу дисциплин
        cursor.execute("""
            CREATE TABLE disciplines (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                competencies TEXT,
                goals TEXT,
                tasks TEXT,
                nltk_normalized_name TEXT,
                nltk_normalized_competencies TEXT,
                nltk_normalized_goals TEXT,
                nltk_normalized_tasks TEXT,
                rubert_vector BLOB
            )
        """)
    
    # Проверяем существование колонки hours в таблице topics
    cursor.execute("""
        PRAGMA table_info(topics)
    """)
    columns = cursor.fetchall()
    has_hours = any(col[1] == 'hours' for col in columns)
    
    if not has_hours:
        # Создаем временную таблицу с новой структурой
        cursor.execute("""
            CREATE TABLE topics_new (
                id INTEGER PRIMARY KEY,
                discipline_id INTEGER,
                title TEXT NOT NULL,
                description TEXT,
                hours INTEGER,
                nltk_normalized_title TEXT,
                nltk_normalized_description TEXT,
                rubert_vector BLOB,
                FOREIGN KEY (discipline_id) REFERENCES disciplines(id)
            )
        """)
        
        # Копируем данные из старой таблицы
        cursor.execute("""
            INSERT INTO topics_new (id, discipline_id, title, description, nltk_normalized_title, nltk_normalized_description, rubert_vector)
            SELECT id, discipline_id, title, description, nltk_normalized_title, nltk_normalized_description, rubert_vector
            FROM topics
        """)
        
        # Удаляем старую таблицу и переименовываем новую
        cursor.execute("DROP TABLE topics")
        cursor.execute("ALTER TABLE topics_new RENAME TO topics")
    
    conn.commit()
    return conn

if __name__ == "__main__":
    update_schema() 