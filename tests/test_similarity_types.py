import pytest
from src.vectorizer import calculate_similarities
from src.text_processor import DatabaseTextProcessor
from src.tfidf_vectorizer import DatabaseVectorizer
from src.rubert_vectorizer import RuBertVectorizer

def test_similarity_types(db_connection):
    """Тест расчета сходства между темами и трудовыми функциями"""
    cursor = db_connection.cursor()
    
    # Создаем необходимые таблицы
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS topics (
            id INTEGER PRIMARY KEY,
            title TEXT,
            description TEXT,
            nltk_normalized_title TEXT,
            nltk_normalized_description TEXT,
            rubert_vector BLOB
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS labor_functions (
            id TEXT PRIMARY KEY,
            name TEXT,
            nltk_normalized_name TEXT,
            rubert_vector BLOB
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS component_types (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        )
    """)
    
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
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS labor_function_components (
            labor_function_id TEXT,
            component_id INTEGER,
            PRIMARY KEY (labor_function_id, component_id),
            FOREIGN KEY (labor_function_id) REFERENCES labor_functions(id),
            FOREIGN KEY (component_id) REFERENCES labor_components(id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS topic_vectors (
            topic_id INTEGER PRIMARY KEY,
            tfidf_vector BLOB,
            rubert_vector BLOB,
            FOREIGN KEY (topic_id) REFERENCES topics(id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS labor_function_vectors (
            labor_function_id TEXT PRIMARY KEY,
            tfidf_vector BLOB,
            rubert_vector BLOB,
            FOREIGN KEY (labor_function_id) REFERENCES labor_functions(id)
        )
    """)
    
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
    
    # Добавляем тестовые данные
    # Добавляем темы
    topics_data = [
        (1, "Python", "Программирование на Python", None, None, None),
        (2, "Web", "Разработка веб-приложений", None, None, None),
        (3, "ML", "Машинное обучение", None, None, None)
    ]
    cursor.executemany(
        "INSERT INTO topics (id, title, description, nltk_normalized_title, nltk_normalized_description, rubert_vector) VALUES (?, ?, ?, ?, ?, ?)",
        topics_data
    )
    
    # Добавляем трудовые функции
    functions_data = [
        ("F1", "Разработка программ", None, None),
        ("F2", "Создание веб-сайтов", None, None),
        ("F3", "Анализ данных", None, None)
    ]
    cursor.executemany(
        "INSERT INTO labor_functions (id, name, nltk_normalized_name, rubert_vector) VALUES (?, ?, ?, ?)",
        functions_data
    )
    
    # Добавляем типы компонентов, если их нет
    cursor.execute("SELECT COUNT(*) FROM component_types")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO component_types (id, name) VALUES
            (1, 'action'),
            (2, 'skill'),
            (3, 'knowledge')
        """)
    
    # Добавляем компоненты
    components_data = [
        (1, 1, "Использование Python", None, None),
        (2, 2, "Работа с фреймворками", None, None),
        (3, 3, "Использование библиотек ML", None, None)
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
    
    db_connection.commit()
    
    # Нормализуем тексты
    text_processor = DatabaseTextProcessor()
    text_processor.process_topics(db_connection)
    text_processor.process_labor_functions(db_connection)
    
    # Векторизуем тексты
    tfidf_vectorizer = DatabaseVectorizer()
    tfidf_vectorizer.vectorize_all(db_connection)
    
    rubert_vectorizer = RuBertVectorizer()
    rubert_vectorizer.vectorize_all(db_connection)
    
    # Проверяем, что таблица topic_labor_function пуста
    cursor.execute("SELECT COUNT(*) FROM topic_labor_function")
    count_before = cursor.fetchone()[0]
    assert count_before == 0
    
    # Рассчитываем сходство
    calculate_similarities(db_connection)
    
    # Проверяем, что появились записи
    cursor.execute("SELECT COUNT(*) FROM topic_labor_function")
    count_after = cursor.fetchone()[0]
    assert count_after > 0
    
    # Проверяем формат данных
    cursor.execute("""
        SELECT tfidf_similarity, rubert_similarity
        FROM topic_labor_function
        LIMIT 1
    """)
    row = cursor.fetchone()
    assert isinstance(row[0], float)  # tfidf_similarity
    assert isinstance(row[1], float)  # rubert_similarity
    assert 0 <= row[0] <= 1  # Сходство должно быть в диапазоне [0, 1]
    assert 0 <= row[1] <= 1 