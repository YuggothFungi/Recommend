import pickle
import numpy as np
from scipy import sparse
import pytest
from src.db import get_db_connection
from src.tfidf_vectorizer import TextVectorizer, DatabaseVectorizer
from src.schema import init_db

@pytest.fixture(scope="function")
def text_vectorizer():
    """Фикстура для создания TextVectorizer"""
    return TextVectorizer()

@pytest.fixture(scope="function")
def db_vectorizer():
    """Фикстура для создания DatabaseVectorizer"""
    return DatabaseVectorizer()

def test_text_vectorizer_initialization(text_vectorizer):
    """Проверка инициализации TextVectorizer"""
    assert text_vectorizer is not None
    assert not text_vectorizer.is_fitted
    assert text_vectorizer.vector_size is None

def test_text_vectorizer_fit(text_vectorizer):
    """Проверка обучения TextVectorizer"""
    texts = ["Тестовый текст 1", "Тестовый текст 2"]
    text_vectorizer.fit(texts)
    assert text_vectorizer.is_fitted
    assert text_vectorizer.vector_size is not None

def test_text_vectorizer_transform(text_vectorizer):
    """Проверка преобразования текста в вектор"""
    texts = ["Тестовый текст 1", "Тестовый текст 2"]
    text_vectorizer.fit(texts)
    text = "Тестовый текст для векторизации"
    vector = text_vectorizer.transform([text])
    assert sparse.issparse(vector)
    assert vector.shape[0] == 1
    assert vector.shape[1] == text_vectorizer.vector_size

def test_db_vectorizer_initialization(db_vectorizer):
    """Проверка инициализации DatabaseVectorizer"""
    assert db_vectorizer is not None
    assert db_vectorizer.vectorizer is not None
    assert isinstance(db_vectorizer.vectorizer, TextVectorizer)

def test_vector_format(db_connection, text_vectorizer):
    """Проверка формата сохраненных векторов"""
    cursor = db_connection.cursor()
    
    # Тестовые данные
    test_data = [
        (1, "Python", "Программирование на Python", None, None, None),
        (2, "Web", "Разработка веб-приложений", None, None, None),
        (3, "ML", "Машинное обучение", None, None, None)
    ]
    
    # Добавление тестовых данных в таблицу topics
    cursor.executemany(
        "INSERT INTO topics (id, title, description, nltk_normalized_title, nltk_normalized_description, rubert_vector) VALUES (?, ?, ?, ?, ?, ?)",
        test_data
    )
    
    # Обучение векторизатора
    texts = [text[2] for text in test_data]  # Используем описание
    text_vectorizer.fit(texts)
    
    # Векторизация и сохранение
    for topic_id, _, text, _, _, _ in test_data:
        vector = text_vectorizer.transform([text])
        vector_bytes = pickle.dumps(vector)
        cursor.execute("""
            INSERT OR REPLACE INTO topic_vectors (topic_id, tfidf_vector)
            VALUES (?, ?)
        """, (topic_id, vector_bytes))
    
    db_connection.commit()
    
    # Проверка формата векторов
    cursor.execute("""
        SELECT tfidf_vector
        FROM topic_vectors
        LIMIT 1
    """)
    vector_bytes = cursor.fetchone()[0]
    vector = pickle.loads(vector_bytes)
    
    assert sparse.issparse(vector)
    assert vector.shape[0] == 1
    assert vector.shape[1] == text_vectorizer.vector_size

def test_vector_similarity(db_connection, text_vectorizer):
    """Проверка косинусного сходства векторов"""
    cursor = db_connection.cursor()
    
    # Тестовые данные
    test_data = [
        (1, "Python", "Программирование на Python", None, None, None),
        (2, "Web", "Разработка веб-приложений", None, None, None),
        (3, "ML", "Машинное обучение", None, None, None)
    ]
    
    # Добавление тестовых данных в таблицу topics
    cursor.executemany(
        "INSERT INTO topics (id, title, description, nltk_normalized_title, nltk_normalized_description, rubert_vector) VALUES (?, ?, ?, ?, ?, ?)",
        test_data
    )
    
    # Обучение векторизатора
    texts = [text[2] for text in test_data]  # Используем описание
    text_vectorizer.fit(texts)
    
    # Векторизация и сохранение
    for topic_id, _, text, _, _, _ in test_data:
        vector = text_vectorizer.transform([text])
        vector_bytes = pickle.dumps(vector)
        cursor.execute("""
            INSERT OR REPLACE INTO topic_vectors (topic_id, tfidf_vector)
            VALUES (?, ?)
        """, (topic_id, vector_bytes))
    
    db_connection.commit()
    
    # Проверка сходства
    cursor.execute("""
        SELECT tfidf_vector
        FROM topic_vectors
        LIMIT 2
    """)
    vectors = [pickle.loads(row[0]) for row in cursor.fetchall()]
    
    # Проверка сходства
    similarity = np.dot(vectors[0].toarray(), vectors[1].toarray().T)[0][0]
    assert 0 <= similarity <= 1

def test_vectors_exist(db_connection, text_vectorizer):
    """Проверка наличия векторов в базе данных"""
    cursor = db_connection.cursor()
    
    # Тестовые данные
    test_data = [
        (1, "Python", "Программирование на Python", None, None, None),
        (2, "Web", "Разработка веб-приложений", None, None, None),
        (3, "ML", "Машинное обучение", None, None, None)
    ]
    
    # Добавление тестовых данных в таблицу topics
    cursor.executemany(
        "INSERT INTO topics (id, title, description, nltk_normalized_title, nltk_normalized_description, rubert_vector) VALUES (?, ?, ?, ?, ?, ?)",
        test_data
    )
    
    # Обучение векторизатора
    texts = [text[2] for text in test_data]  # Используем описание
    text_vectorizer.fit(texts)
    
    # Векторизация и сохранение
    for topic_id, _, text, _, _, _ in test_data:
        vector = text_vectorizer.transform([text])
        vector_bytes = pickle.dumps(vector)
        cursor.execute("""
            INSERT OR REPLACE INTO topic_vectors (topic_id, tfidf_vector)
            VALUES (?, ?)
        """, (topic_id, vector_bytes))
    
    db_connection.commit()
    
    # Проверка количества векторов
    cursor.execute("SELECT COUNT(*) FROM topic_vectors")
    count = cursor.fetchone()[0]
    assert count == len(test_data) 