import sqlite3
from db import get_db_connection

def init_db():
    """Инициализация базы данных с созданием всех необходимых таблиц"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Создание таблиц
    cursor.executescript("""
    -- Учебные темы
    CREATE TABLE IF NOT EXISTS topics (
        id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT,
        hours INTEGER,
        semester INTEGER,
        section_number INTEGER,
        pymorphy2_nltk_normalized_title TEXT,
        pymorphy2_nltk_normalized_description TEXT
    );

    -- Компетенции
    CREATE TABLE IF NOT EXISTS competencies (
        id TEXT PRIMARY KEY,
        category TEXT,
        description TEXT,
        pymorphy2_nltk_normalized_category TEXT,
        pymorphy2_nltk_normalized_description TEXT
    );

    -- Трудовые функции
    CREATE TABLE IF NOT EXISTS labor_functions (
        id TEXT PRIMARY KEY,
        code TEXT,
        name TEXT,
        qualification_level INTEGER,
        pymorphy2_nltk_normalized_name TEXT
    );

    -- Типы компонентов (справочник)
    CREATE TABLE IF NOT EXISTS component_types (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL  -- "action", "skill", "knowledge"
    );

    -- Общие компоненты (действия/умения/знания)
    CREATE TABLE IF NOT EXISTS labor_components (
        id INTEGER PRIMARY KEY,
        component_type_id INTEGER,
        description TEXT NOT NULL,
        pymorphy2_nltk_normalized_description TEXT,
        FOREIGN KEY (component_type_id) REFERENCES component_types(id)
    );

    -- Связь трудовых функций и компонентов
    CREATE TABLE IF NOT EXISTS labor_function_components (
        labor_function_id TEXT,
        component_id INTEGER,
        FOREIGN KEY (labor_function_id) REFERENCES labor_functions(id),
        FOREIGN KEY (component_id) REFERENCES labor_components(id),
        PRIMARY KEY (labor_function_id, component_id)
    );

    -- Связь тем и компетенций
    CREATE TABLE IF NOT EXISTS topic_competency (
        topic_id INTEGER,
        competency_id TEXT,
        FOREIGN KEY (topic_id) REFERENCES topics(id),
        FOREIGN KEY (competency_id) REFERENCES competencies(id)
    );

    -- Связь тем и трудовых функций
    CREATE TABLE IF NOT EXISTS topic_labor_function (
        topic_id INTEGER,
        labor_function_id TEXT,
        similarity_score REAL,
        FOREIGN KEY (topic_id) REFERENCES topics(id),
        FOREIGN KEY (labor_function_id) REFERENCES labor_functions(id)
    );
    """)
    
    # Заполнение справочника типов компонентов
    cursor.executescript("""
    INSERT OR IGNORE INTO component_types (id, name) VALUES
    (1, 'action'),
    (2, 'skill'),
    (3, 'knowledge');
    """)
    
    conn.commit()
    conn.close()

def reset_db():
    """Сброс базы данных (удаление всех таблиц)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Получаем список всех таблиц
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    # Удаляем каждую таблицу
    for table in tables:
        cursor.execute(f"DROP TABLE IF EXISTS {table[0]};")
    
    conn.commit()
    conn.close()
    
    # Создаем базу данных заново
    init_db()

if __name__ == "__main__":
    reset_db() 