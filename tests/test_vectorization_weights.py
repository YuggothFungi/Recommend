import pytest
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from src.vectorization_config import VectorizationConfig
from src.tfidf_vectorizer import TfidfDatabaseVectorizer
from src.rubert_vectorizer import RuBertVectorizer
from src.vectorization_text_weights import VectorizationTextWeights
from src.db import get_db_connection

@pytest.fixture(scope="function")
def db_connection():
    """Фикстура для создания соединения с базой данных"""
    conn = get_db_connection()
    yield conn
    conn.close()

@pytest.fixture
def config_basic():
    """Фикстура для базовой конфигурации (только основные сущности)"""
    return VectorizationConfig(1)

@pytest.fixture
def config_full():
    """Фикстура для полной конфигурации (все сущности)"""
    return VectorizationConfig(3)

@pytest.fixture
def text_weights_basic(config_basic):
    """Фикстура для текстовых весов с базовой конфигурацией"""
    return VectorizationTextWeights(config_basic)

@pytest.fixture
def text_weights_full(config_full):
    """Фикстура для текстовых весов с полной конфигурацией"""
    return VectorizationTextWeights(config_full)

@pytest.fixture
def tfidf_vectorizer_basic(config_basic):
    """Фикстура для TF-IDF векторайзера с базовой конфигурацией"""
    return TfidfDatabaseVectorizer(config_basic)

@pytest.fixture
def tfidf_vectorizer_full(config_full):
    """Фикстура для TF-IDF векторайзера с полной конфигурацией"""
    return TfidfDatabaseVectorizer(config_full)

@pytest.fixture
def rubert_vectorizer_basic(config_basic):
    """Фикстура для RuBERT векторайзера с базовой конфигурацией"""
    return RuBertVectorizer(config_basic.config_id)

@pytest.fixture
def rubert_vectorizer_full(config_full):
    """Фикстура для RuBERT векторайзера с полной конфигурацией"""
    return RuBertVectorizer(config_full.config_id)

def test_tfidf_vectorization_weights():
    """Тест проверяет, что разные конфигурации дают разные векторы для TF-IDF"""
    # Создаем конфигурации
    config1 = VectorizationConfig(1)  # Только базовые сущности
    config3 = VectorizationConfig(3)  # Полный контекст
    
    # Подключаемся к БД
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Создаем векторизаторы
    tfidf_vectorizer = TfidfDatabaseVectorizer(config1)  # Используем один векторизатор
    text_weights1 = VectorizationTextWeights(config1)
    text_weights3 = VectorizationTextWeights(config3)
    
    # Получаем все ID из базы
    cursor.execute("SELECT id FROM lecture_topics")
    lecture_ids = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT id FROM practical_topics")
    practical_ids = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT id FROM labor_functions")
    labor_ids = [row[0] for row in cursor.fetchall()]
    
    # Собираем все тексты для обучения
    all_texts = []
    
    # Лекционные темы
    for lt_id in lecture_ids:
        text1, _ = text_weights1.get_lecture_topic_text(lt_id, conn)
        text3, _ = text_weights3.get_lecture_topic_text(lt_id, conn)
        all_texts.extend([text1, text3])
    
    # Практические темы
    for pt_id in practical_ids:
        text1, _ = text_weights1.get_practical_topic_text(pt_id, conn)
        text3, _ = text_weights3.get_practical_topic_text(pt_id, conn)
        all_texts.extend([text1, text3])
    
    # Трудовые функции
    for lf_id in labor_ids:
        text1 = text_weights1.get_labor_function_text(lf_id, conn)
        text3 = text_weights3.get_labor_function_text(lf_id, conn)
        all_texts.extend([text1, text3])
    
    # Обучаем векторизатор
    tfidf_vectorizer.fit(all_texts)
    
    # Проверяем лекционные темы
    for lt_id in lecture_ids:
        # Получаем тексты
        text1, _ = text_weights1.get_lecture_topic_text(lt_id, conn)
        text3, _ = text_weights3.get_lecture_topic_text(lt_id, conn)
        # TF-IDF векторизация
        tfidf_vector1 = tfidf_vectorizer.transform([text1])[0]
        tfidf_vector3 = tfidf_vectorizer.transform([text3])[0]
        # Проверяем, что векторы разные
        tfidf_similarity = cosine_similarity(tfidf_vector1.reshape(1, -1), tfidf_vector3.reshape(1, -1))[0][0]
        assert tfidf_similarity < 1.0, f"TF-IDF векторы идентичны для лекционной темы {lt_id}"
    
    # Проверяем практические темы
    for pt_id in practical_ids:
        text1, _ = text_weights1.get_practical_topic_text(pt_id, conn)
        text3, _ = text_weights3.get_practical_topic_text(pt_id, conn)
        tfidf_vector1 = tfidf_vectorizer.transform([text1])[0]
        tfidf_vector3 = tfidf_vectorizer.transform([text3])[0]
        tfidf_similarity = cosine_similarity(tfidf_vector1.reshape(1, -1), tfidf_vector3.reshape(1, -1))[0][0]
        assert tfidf_similarity < 1.0, f"TF-IDF векторы идентичны для практической темы {pt_id}"
    
    # Проверяем трудовые функции
    for lf_id in labor_ids:
        text1 = text_weights1.get_labor_function_text(lf_id, conn)
        text3 = text_weights3.get_labor_function_text(lf_id, conn)
        tfidf_vector1 = tfidf_vectorizer.transform([text1])[0]
        tfidf_vector3 = tfidf_vectorizer.transform([text3])[0]
        tfidf_similarity = cosine_similarity(tfidf_vector1.reshape(1, -1), tfidf_vector3.reshape(1, -1))[0][0]
        assert tfidf_similarity < 1.0, f"TF-IDF векторы идентичны для трудовой функции {lf_id}"
    
    conn.close()

def test_rubert_vectorization_weights():
    """Тест проверяет, что разные конфигурации дают разные векторы для RuBERT"""
    # Создаем конфигурации
    config1 = VectorizationConfig(1)  # Только базовые сущности
    config3 = VectorizationConfig(3)  # Полный контекст
    
    # Подключаемся к БД
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Создаем векторизаторы
    rubert_vectorizer1 = RuBertVectorizer(config1.config_id)
    rubert_vectorizer3 = RuBertVectorizer(config3.config_id)
    text_weights1 = VectorizationTextWeights(config1)
    text_weights3 = VectorizationTextWeights(config3)
    
    # Получаем все ID из базы
    cursor.execute("SELECT id FROM lecture_topics")
    lecture_ids = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT id FROM practical_topics")
    practical_ids = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT id FROM labor_functions")
    labor_ids = [row[0] for row in cursor.fetchall()]
    
    # Проверяем лекционные темы
    for lt_id in lecture_ids:
        # Получаем тексты
        text1, _ = text_weights1.get_lecture_topic_text(lt_id, conn)
        text3, _ = text_weights3.get_lecture_topic_text(lt_id, conn)
        # RuBERT векторизация
        rubert_vector1 = rubert_vectorizer1.get_vector(text1)
        rubert_vector3 = rubert_vectorizer3.get_vector(text3)
        # Проверяем, что векторы разные
        rubert_similarity = cosine_similarity(rubert_vector1.reshape(1, -1), rubert_vector3.reshape(1, -1))[0][0]
        assert rubert_similarity < 1.0, f"RuBERT векторы идентичны для лекционной темы {lt_id}"
    
    # Проверяем практические темы
    for pt_id in practical_ids:
        text1, _ = text_weights1.get_practical_topic_text(pt_id, conn)
        text3, _ = text_weights3.get_practical_topic_text(pt_id, conn)
        rubert_vector1 = rubert_vectorizer1.get_vector(text1)
        rubert_vector3 = rubert_vectorizer3.get_vector(text3)
        rubert_similarity = cosine_similarity(rubert_vector1.reshape(1, -1), rubert_vector3.reshape(1, -1))[0][0]
        assert rubert_similarity < 1.0, f"RuBERT векторы идентичны для практической темы {pt_id}"
    
    # Проверяем трудовые функции
    for lf_id in labor_ids:
        text1 = text_weights1.get_labor_function_text(lf_id, conn)
        text3 = text_weights3.get_labor_function_text(lf_id, conn)
        rubert_vector1 = rubert_vectorizer1.get_vector(text1)
        rubert_vector3 = rubert_vectorizer3.get_vector(text3)
        rubert_similarity = cosine_similarity(rubert_vector1.reshape(1, -1), rubert_vector3.reshape(1, -1))[0][0]
        assert rubert_similarity < 1.0, f"RuBERT векторы идентичны для трудовой функции {lf_id}"
    
    conn.close() 