import pytest
import numpy as np
from src.rubert_vectorizer import RuBertVectorizer
import sqlite3
from src.db import get_db_connection
from src.schema import init_db

@pytest.fixture(scope="session")
def db_connection():
    """Фикстура для создания соединения с базой данных"""
    conn = get_db_connection()
    yield conn
    conn.close()

@pytest.fixture(autouse=True)
def clean_db(db_connection):
    """Фикстура для очистки базы данных перед каждым тестом"""
    cursor = db_connection.cursor()
    # Удаляем все временные таблицы
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name LIKE 'test_%'
    """)
    tables = cursor.fetchall()
    for table in tables:
        cursor.execute(f"DROP TABLE IF EXISTS {table[0]}")
    db_connection.commit()

@pytest.fixture
def vectorizer():
    """Создание экземпляра RuBertVectorizer"""
    return RuBertVectorizer()

@pytest.fixture
def test_texts():
    """Тестовые тексты"""
    return [
        "Программирование на Python",
        "Разработка веб-приложений",
        "Машинное обучение"
    ]

def test_transform(vectorizer, test_texts):
    """Тест метода transform"""
    vectors = vectorizer.transform(test_texts)
    
    # Проверяем размерность векторов
    assert vectors.shape[0] == len(test_texts)
    assert vectors.shape[1] == 1024  # Размерность вектора sbert_large_nlu_ru
    
    # Проверяем тип данных
    assert isinstance(vectors, np.ndarray)
    assert vectors.dtype == np.float32
    
    # Проверяем нормализацию
    for i in range(vectors.shape[0]):
        norm = np.linalg.norm(vectors[i])
        assert abs(norm - 1.0) < 1e-6  # Векторы должны быть нормализованы

def test_get_vector(vectorizer, test_texts):
    """Тест метода get_vector"""
    vector = vectorizer.get_vector(test_texts[0])
    
    # Проверяем размерность вектора
    assert vector.shape == (1024,)  # Размерность вектора sbert_large_nlu_ru
    
    # Проверяем тип данных
    assert isinstance(vector, np.ndarray)
    assert vector.dtype == np.float32
    
    # Проверяем нормализацию
    norm = np.linalg.norm(vector)
    assert abs(norm - 1.0) < 1e-6

def test_get_similarity(vectorizer, test_texts):
    """Тест метода get_similarity"""
    similarity = vectorizer.get_similarity(test_texts[0], test_texts[1])
    
    # Проверяем тип данных
    assert isinstance(similarity, np.float32)
    
    # Проверяем диапазон значений
    assert 0 <= similarity <= 1

def test_vectorize_table(vectorizer, db_connection):
    """Тест метода _vectorize_table"""
    cursor = db_connection.cursor()
    
    # Создаем таблицу для теста
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_table (
            id INTEGER PRIMARY KEY,
            text TEXT,
            rubert_vector BLOB
        )
    """)
    
    # Добавляем тестовые данные
    test_data = [
        (1, "Программирование на Python"),
        (2, "Разработка веб-приложений"),
        (3, "Машинное обучение")
    ]
    cursor.executemany(
        "INSERT INTO test_table (id, text) VALUES (?, ?)",
        test_data
    )
    
    db_connection.commit()
    
    # Векторизуем таблицу
    vectorizer._vectorize_table("test_table", "text")
    
    # Проверяем, что векторы добавлены
    cursor.execute("SELECT rubert_vector FROM test_table")
    vectors = cursor.fetchall()
    assert len(vectors) == len(test_data)
    for vector, in vectors:
        assert vector is not None
    
    # Очищаем тестовую таблицу
    cursor.execute("DROP TABLE test_table")
    db_connection.commit()

def test_vectorize_all(vectorizer, db_connection):
    """Тест метода vectorize_all"""
    cursor = db_connection.cursor()
    
    # Очищаем таблицы перед тестом
    cursor.execute("DROP TABLE IF EXISTS topic_vectors")
    cursor.execute("DROP TABLE IF EXISTS labor_function_vectors")
    cursor.execute("DROP TABLE IF EXISTS labor_function_components")
    cursor.execute("DROP TABLE IF EXISTS labor_components")
    cursor.execute("DROP TABLE IF EXISTS component_types")
    cursor.execute("DROP TABLE IF EXISTS labor_functions")
    cursor.execute("DROP TABLE IF EXISTS topics")
    
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
    
    # Добавляем тестовые данные
    topics_data = [
        (1, "Python", "Программирование на Python", "python", "программирование python", None),
        (2, "Web", "Разработка веб-приложений", "web", "разработка веб приложений", None),
        (3, "ML", "Машинное обучение", "ml", "машинное обучение", None)
    ]
    cursor.executemany(
        "INSERT INTO topics (id, title, description, nltk_normalized_title, nltk_normalized_description, rubert_vector) VALUES (?, ?, ?, ?, ?, ?)",
        topics_data
    )
    
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
    
    db_connection.commit()
    
    # Векторизуем все таблицы
    vectorizer.vectorize_all()
    
    # Проверяем, что векторы добавлены
    cursor.execute("SELECT rubert_vector FROM topic_vectors")
    vectors = cursor.fetchall()
    assert len(vectors) == len(topics_data)
    for vector, in vectors:
        assert vector is not None
    
    cursor.execute("SELECT rubert_vector FROM labor_function_vectors")
    vectors = cursor.fetchall()
    assert len(vectors) == len(functions_data)
    for vector, in vectors:
        assert vector is not None 