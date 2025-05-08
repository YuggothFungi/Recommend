import os
from src.db import get_db_connection

def init_db():
    """Инициализация базы данных"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Дисциплины - основная таблица для учебных дисциплин
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS disciplines (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            goals TEXT,
            tasks TEXT,
            nltk_normalized_name TEXT,
            nltk_normalized_goals TEXT,
            nltk_normalized_tasks TEXT,
            rubert_vector BLOB
        )
    """)
    
    # Семестры - независимая таблица для семестров учебного года
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS semesters (
            id INTEGER PRIMARY KEY,
            number INTEGER NOT NULL UNIQUE
        )
    """)
    
    # Предзаполнение таблицы семестров
    cursor.execute("""
        INSERT OR IGNORE INTO semesters (id, number) VALUES
        (1, 1), (2, 2), (3, 3), (4, 4),
        (5, 5), (6, 6), (7, 7), (8, 8)
    """)
    
    # Связь дисциплин и семестров - многие-ко-многим
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS discipline_semesters (
            discipline_id INTEGER,
            semester_id INTEGER,
            PRIMARY KEY (discipline_id, semester_id),
            FOREIGN KEY (discipline_id) REFERENCES disciplines(id),
            FOREIGN KEY (semester_id) REFERENCES semesters(id)
        )
    """)
    
    # Разделы - связаны с дисциплинами и семестрами
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sections (
            id INTEGER PRIMARY KEY,
            discipline_id INTEGER,
            semester_id INTEGER,
            number INTEGER,
            name TEXT NOT NULL,
            content TEXT,
            nltk_normalized_name TEXT,
            nltk_normalized_content TEXT,
            rubert_vector BLOB,
            FOREIGN KEY (discipline_id) REFERENCES disciplines(id),
            FOREIGN KEY (semester_id) REFERENCES semesters(id),
            UNIQUE (discipline_id, semester_id, number)
        )
    """)
    
    # Темы лекций - связаны с разделами
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lecture_topics (
            id INTEGER PRIMARY KEY,
            section_id INTEGER,
            name TEXT NOT NULL,
            hours REAL,
            nltk_normalized_name TEXT,
            rubert_vector BLOB,
            FOREIGN KEY (section_id) REFERENCES sections(id)
        )
    """)
    
    # Темы практических занятий - связаны с разделами
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS practical_topics (
            id INTEGER PRIMARY KEY,
            section_id INTEGER,
            name TEXT NOT NULL,
            hours REAL,
            nltk_normalized_name TEXT,
            rubert_vector BLOB,
            FOREIGN KEY (section_id) REFERENCES sections(id)
        )
    """)
    
    # Вопросы для самоконтроля - связаны с разделами
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS self_control_questions (
            id INTEGER PRIMARY KEY,
            section_id INTEGER,
            question TEXT NOT NULL,
            nltk_normalized_question TEXT,
            rubert_vector BLOB,
            FOREIGN KEY (section_id) REFERENCES sections(id)
        )
    """)
    
    # Компетенции - основная таблица для компетенций
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
    
    # Связь дисциплин с компетенциями - многие-ко-многим
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS discipline_competencies (
            discipline_id INTEGER,
            competency_id TEXT,
            PRIMARY KEY (discipline_id, competency_id),
            FOREIGN KEY (discipline_id) REFERENCES disciplines(id),
            FOREIGN KEY (competency_id) REFERENCES competencies(id)
        )
    """)
    
    # Специальности из профессиональных стандартов
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS specialties (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            nltk_normalized_name TEXT
        )
    """)
    
    # Трудовые функции
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS labor_functions (
            id TEXT PRIMARY KEY,
            code TEXT,
            name TEXT NOT NULL,
            qualification_level INTEGER,
            nltk_normalized_name TEXT,
            rubert_vector BLOB
        )
    """)
    
    # Связь специальностей с трудовыми функциями
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS specialty_labor_functions (
            specialty_id INTEGER,
            labor_function_id TEXT,
            PRIMARY KEY (specialty_id, labor_function_id),
            FOREIGN KEY (specialty_id) REFERENCES specialties(id),
            FOREIGN KEY (labor_function_id) REFERENCES labor_functions(id)
        )
    """)
    
    # Типы компонентов трудовых функций
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS component_types (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        )
    """)
    
    # Компоненты трудовых функций
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS labor_components (
            id INTEGER PRIMARY KEY,
            labor_function_id TEXT,
            component_type_id INTEGER,
            description TEXT NOT NULL,
            nltk_normalized_description TEXT,
            rubert_vector BLOB,
            FOREIGN KEY (labor_function_id) REFERENCES labor_functions(id),
            FOREIGN KEY (component_type_id) REFERENCES component_types(id)
        )
    """)
    
    # Заполнение справочника типов компонентов
    cursor.execute("""
        INSERT OR IGNORE INTO component_types (id, name) VALUES
        (1, 'трудовые_действия'),
        (2, 'необходимые_умения'),
        (3, 'необходимые_знания'),
        (4, 'другие_характеристики')
    """)
    
    conn.commit()
    return conn

def reset_db():
    """Сброс базы данных"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Удаление таблиц связей (многие-ко-многим)
    cursor.execute("DROP TABLE IF EXISTS specialty_labor_functions")
    cursor.execute("DROP TABLE IF EXISTS topic_competencies")
    cursor.execute("DROP TABLE IF EXISTS discipline_competencies")
    cursor.execute("DROP TABLE IF EXISTS discipline_semesters")
    
    # Удаление таблиц с внешними ключами
    cursor.execute("DROP TABLE IF EXISTS labor_components")
    cursor.execute("DROP TABLE IF EXISTS lecture_topics")
    cursor.execute("DROP TABLE IF EXISTS practical_topics")
    cursor.execute("DROP TABLE IF EXISTS self_control_questions")
    cursor.execute("DROP TABLE IF EXISTS sections")
    
    # Удаление основных таблиц
    cursor.execute("DROP TABLE IF EXISTS component_types")
    cursor.execute("DROP TABLE IF EXISTS labor_functions")
    cursor.execute("DROP TABLE IF EXISTS specialties")
    cursor.execute("DROP TABLE IF EXISTS competencies")
    cursor.execute("DROP TABLE IF EXISTS semesters")
    cursor.execute("DROP TABLE IF EXISTS disciplines")
    
    conn.commit()
    return conn


if __name__ == "__main__":
    init_db()
