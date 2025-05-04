import pytest
import numpy as np
from src.vectorizer import calculate_similarities
from src.text_processor import DatabaseTextProcessor
from src.vectorizer import DatabaseVectorizer
from src.rubert_vectorizer import RuBertVectorizer
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

def test_similarity_types(db_connection):
    """Тест расчета сходства между темами и трудовыми функциями"""
    cursor = db_connection.cursor()
    
    # Создаем таблицы и добавляем тестовые данные
    create_test_tables(cursor)
    insert_test_data(cursor)
    db_connection.commit()
    
    # Нормализуем тексты
    text_processor = DatabaseTextProcessor()
    text_processor.process_topics(db_connection)
    text_processor.process_labor_functions(db_connection)
    text_processor.process_labor_components(db_connection)
    
    # Проверяем, что тексты нормализованы
    cursor.execute("SELECT COUNT(*) FROM topics WHERE nltk_normalized_title IS NULL OR nltk_normalized_description IS NULL")
    assert cursor.fetchone()[0] == 0
    
    cursor.execute("SELECT COUNT(*) FROM labor_functions WHERE nltk_normalized_name IS NULL")
    assert cursor.fetchone()[0] == 0
    
    cursor.execute("SELECT COUNT(*) FROM labor_components WHERE nltk_normalized_description IS NULL")
    assert cursor.fetchone()[0] == 0
    
    # Векторизуем тексты
    tfidf_vectorizer = DatabaseVectorizer()
    tfidf_vectorizer.vectorize_all(db_connection)
    
    rubert_vectorizer = RuBertVectorizer()
    rubert_vectorizer.vectorize_all(db_connection)
    
    # Проверяем, что векторы сохранены
    cursor.execute("SELECT COUNT(*) FROM topic_vectors")
    assert cursor.fetchone()[0] == 3  # Количество тем
    
    cursor.execute("SELECT COUNT(*) FROM labor_function_vectors")
    assert cursor.fetchone()[0] == 3  # Количество трудовых функций
    
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