"""Вспомогательные функции для тестов"""

def create_test_tables(cursor):
    """Создание тестовых таблиц"""
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
            nltk_normalized_title TEXT,
            nltk_normalized_description TEXT,
            rubert_vector BLOB,
            FOREIGN KEY (discipline_id) REFERENCES disciplines(id)
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

def insert_test_data(cursor):
    """Вставка тестовых данных"""
    # Добавляем дисциплину
    cursor.execute("""
        INSERT INTO disciplines (id, name, competencies, goals, tasks) 
        VALUES (1, 'Программирование', 'Компетенции', 'Цели', 'Задачи')
    """)
    
    # Добавляем темы
    topics_data = [
        (1, 1, "Python", "Программирование на Python", "python", "программирование python", None),
        (2, 1, "Web", "Разработка веб-приложений", "web", "разработка веб приложений", None),
        (3, 1, "ML", "Машинное обучение", "ml", "машинное обучение", None)
    ]
    cursor.executemany(
        "INSERT INTO topics (id, discipline_id, title, description, nltk_normalized_title, nltk_normalized_description, rubert_vector) VALUES (?, ?, ?, ?, ?, ?, ?)",
        topics_data
    )
    
    # Добавляем трудовые функции
    functions_data = [
        ("F1", "Разработка программ", "разработка программ", None),
        ("F2", "Создание веб-сайтов", "создание веб сайтов", None),
        ("F3", "Анализ данных", "анализ данных", None)
    ]
    cursor.executemany(
        "INSERT INTO labor_functions (id, name, nltk_normalized_name, rubert_vector) VALUES (?, ?, ?, ?)",
        functions_data
    )
    
    # Добавляем типы компонентов
    cursor.execute("""
        INSERT INTO component_types (id, name) VALUES
        (1, 'action'),
        (2, 'skill'),
        (3, 'knowledge')
    """)
    
    # Добавляем компоненты
    components_data = [
        (1, 1, "Использование Python", "использование python", None),
        (2, 2, "Работа с фреймворками", "работа фреймворки", None),
        (3, 3, "Использование библиотек ML", "использование библиотеки ml", None)
    ]
    cursor.executemany(
        "INSERT INTO labor_components (id, component_type_id, description, nltk_normalized_description, rubert_vector) VALUES (?, ?, ?, ?, ?)",
        components_data
    )
    
    # Связываем трудовые функции и компоненты
    function_components = [
        ("F1", 1),
        ("F2", 2),
        ("F3", 3)
    ]
    cursor.executemany(
        "INSERT INTO labor_function_components (labor_function_id, component_id) VALUES (?, ?)",
        function_components
    )

def clean_test_tables(cursor):
    """Очистка тестовых таблиц"""
    cursor.execute("DROP TABLE IF EXISTS topic_labor_function")
    cursor.execute("DROP TABLE IF EXISTS topic_vectors")
    cursor.execute("DROP TABLE IF EXISTS labor_function_vectors")
    cursor.execute("DROP TABLE IF EXISTS labor_function_components")
    cursor.execute("DROP TABLE IF EXISTS labor_components")
    cursor.execute("DROP TABLE IF EXISTS component_types")
    cursor.execute("DROP TABLE IF EXISTS labor_functions")
    cursor.execute("DROP TABLE IF EXISTS topics")
    cursor.execute("DROP TABLE IF EXISTS disciplines") 