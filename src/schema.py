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
    
    # Таблица конфигураций векторизации
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vectorization_configurations (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            config_type TEXT NOT NULL CHECK (config_type IN ('l1_p1', 'l1l2_p1p2', 'l1l2l3_p1p2')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Таблица весов для источников текста
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vectorization_weights (
            id INTEGER PRIMARY KEY,
            configuration_id INTEGER NOT NULL,
            entity_type TEXT NOT NULL CHECK (entity_type IN ('lecture_topic', 'practical_topic', 'labor_function')),
            source_type TEXT NOT NULL,
            use_normalized BOOLEAN DEFAULT TRUE,
            weight REAL DEFAULT 1.0,
            hours_weight REAL DEFAULT 1.0,
            FOREIGN KEY (configuration_id) REFERENCES vectorization_configurations(id) ON DELETE CASCADE
        )
    """)
    
    # Таблица результатов векторизации
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vectorization_results (
            id INTEGER PRIMARY KEY,
            configuration_id INTEGER NOT NULL,
            entity_type TEXT NOT NULL CHECK (entity_type IN ('lecture_topic', 'practical_topic', 'labor_function')),
            entity_id INTEGER NOT NULL,
            vector_type TEXT NOT NULL CHECK (vector_type IN ('tfidf', 'rubert')),
            vector_data BLOB NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (configuration_id) REFERENCES vectorization_configurations(id) ON DELETE CASCADE
        )
    """)
    
    # Таблица результатов сходства
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS similarity_results (
            id INTEGER PRIMARY KEY,
            configuration_id INTEGER NOT NULL,
            topic_id INTEGER NOT NULL,
            topic_type TEXT NOT NULL CHECK (topic_type IN ('lecture', 'practical')),
            labor_function_id TEXT NOT NULL,
            rubert_similarity REAL NOT NULL,
            tfidf_similarity REAL NOT NULL,
            topic_hours REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (configuration_id) REFERENCES vectorization_configurations(id) ON DELETE CASCADE
        )
    """)
    
    # Индексы для оптимизации запросов
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_vectorization_weights_config 
        ON vectorization_weights(configuration_id)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_vectorization_weights_entity 
        ON vectorization_weights(entity_type)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_vectorization_results_config 
        ON vectorization_results(configuration_id)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_vectorization_results_entity 
        ON vectorization_results(entity_type, entity_id)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_similarity_results_config 
        ON similarity_results(configuration_id)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_similarity_results_topic 
        ON similarity_results(topic_type, topic_id)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_similarity_results_function 
        ON similarity_results(labor_function_id)
    """)
    
    # Уникальный индекс для предотвращения дублирования записей
    cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_similarity_results_unique 
        ON similarity_results(configuration_id, topic_id, topic_type, labor_function_id)
    """)
    
    # Предопределенные конфигурации
    cursor.execute("""
        INSERT OR IGNORE INTO vectorization_configurations (name, description, config_type) VALUES
        ('Только базовые сущности', 'Векторизация только названий тем и трудовых функций', 'l1_p1'),
        ('Базовые сущности + контекст раздела', 'Векторизация с учетом контекста раздела и компонентов', 'l1l2_p1p2'),
        ('Полный контекст', 'Векторизация с учетом полного контекста', 'l1l2l3_p1p2')
    """)
    
    # Веса для конфигурации l1_p1
    cursor.execute("""
        INSERT OR IGNORE INTO vectorization_weights (configuration_id, entity_type, source_type, weight) VALUES
        (1, 'lecture_topic', 'name', 1.0),
        (1, 'practical_topic', 'name', 1.0),
        (1, 'labor_function', 'name', 1.0)
    """)
    
    # Веса для конфигурации l1l2_p1p2
    cursor.execute("""
        INSERT OR IGNORE INTO vectorization_weights (configuration_id, entity_type, source_type, weight) VALUES
        (2, 'lecture_topic', 'name', 1.0),
        (2, 'lecture_topic', 'section_name', 0.5),
        (2, 'lecture_topic', 'section_content', 0.5),
        (2, 'lecture_topic', 'self_control_questions', 0.3),
        (2, 'practical_topic', 'name', 1.0),
        (2, 'practical_topic', 'section_name', 0.5),
        (2, 'practical_topic', 'section_content', 0.5),
        (2, 'practical_topic', 'self_control_questions', 0.3),
        (2, 'labor_function', 'name', 1.0),
        (2, 'labor_function', 'labor_components', 0.7)
    """)
    
    # Веса для конфигурации l1l2l3_p1p2
    cursor.execute("""
        INSERT OR IGNORE INTO vectorization_weights (configuration_id, entity_type, source_type, weight) VALUES
        (3, 'lecture_topic', 'name', 1.0),
        (3, 'lecture_topic', 'section_name', 0.5),
        (3, 'lecture_topic', 'section_content', 0.5),
        (3, 'lecture_topic', 'self_control_questions', 0.3),
        (3, 'lecture_topic', 'discipline_goals', 0.3),
        (3, 'lecture_topic', 'discipline_tasks', 0.3),
        (3, 'practical_topic', 'name', 1.0),
        (3, 'practical_topic', 'section_name', 0.5),
        (3, 'practical_topic', 'section_content', 0.5),
        (3, 'practical_topic', 'self_control_questions', 0.3),
        (3, 'practical_topic', 'discipline_goals', 0.3),
        (3, 'practical_topic', 'discipline_tasks', 0.3),
        (3, 'labor_function', 'name', 1.0),
        (3, 'labor_function', 'labor_components', 0.7)
    """)
    
    conn.commit()
    return conn

def reset_db():
    """Сброс базы данных"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Удаление таблиц векторизации
    cursor.execute("DROP TABLE IF EXISTS similarity_results")
    cursor.execute("DROP TABLE IF EXISTS vectorization_results")
    cursor.execute("DROP TABLE IF EXISTS vectorization_weights")
    cursor.execute("DROP TABLE IF EXISTS vectorization_configurations")
    
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
