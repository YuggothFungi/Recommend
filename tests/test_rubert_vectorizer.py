import pytest
import numpy as np
from src.rubert_vectorizer import RuBertVectorizer
import sqlite3
from src.db import get_db_connection
from src.schema import init_db
from tests.test_utils import create_test_tables, insert_test_data, clean_test_tables

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
    clean_test_tables(cursor)
    db_connection.commit()

@pytest.fixture
def vectorizer(db_connection):
    """Создание экземпляра RuBertVectorizer"""
    return RuBertVectorizer(conn=db_connection)

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
    vectorizer._vectorize_table("test_table", "text", conn=db_connection)
    
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
    
    # Создаем таблицы и добавляем тестовые данные
    create_test_tables(cursor)
    insert_test_data(cursor)
    db_connection.commit()
    
    # Векторизуем все таблицы
    vectorizer.vectorize_all()
    
    # Проверяем, что векторы добавлены
    cursor.execute("SELECT rubert_vector FROM topic_vectors")
    vectors = cursor.fetchall()
    assert len(vectors) == 3  # Количество тем
    
    cursor.execute("SELECT rubert_vector FROM labor_function_vectors")
    vectors = cursor.fetchall()
    assert len(vectors) == 3  # Количество трудовых функций 