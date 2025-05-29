import pytest
from src.tfidf_vectorizer import TfidfDatabaseVectorizer
from src.vectorization_config import VectorizationConfig
from src.vector_storage import VectorStorage
from src.db import get_db_connection

@pytest.mark.usefixtures("db_connection")
class TestKeywords:
    """Тесты для работы с ключевыми словами"""
    
    def test_keywords_save_and_get(self, db_connection):
        """Тест сохранения и получения ключевых слов"""
        # Создаем тестовые данные
        test_texts = [
            "тестовая тема 1",
            "тестовая тема 2",
            "тестовая функция 1",
            "тестовая функция 2"
        ]
        
        # Инициализируем компоненты
        config_id = 1
        config = VectorizationConfig(config_id)
        vectorizer = TfidfDatabaseVectorizer(config)
        storage = VectorStorage(config_id)
        
        # Обучаем векторизатор
        vectorizer.fit(test_texts)
        
        # Извлекаем ключевые слова для каждого текста
        keywords = {}
        keywords['lecture_topic'] = {
            1: vectorizer.extract_keywords(test_texts[0]),
            2: vectorizer.extract_keywords(test_texts[1])
        }
        keywords['labor_function'] = {
            '3.1.1': vectorizer.extract_keywords(test_texts[2]),
            '3.1.2': vectorizer.extract_keywords(test_texts[3])
        }
        
        # Сохраняем ключевые слова
        storage.save_keywords(config_id, keywords)
        
        # Получаем ключевые слова
        saved_keywords = storage.get_keywords(config_id)
        
        # Проверяем результаты
        assert 'lecture_topic' in saved_keywords
        assert 'labor_function' in saved_keywords
        
        # Проверяем ключевые слова для тем
        topic_keywords = saved_keywords['lecture_topic']
        assert 1 in topic_keywords
        assert 2 in topic_keywords
        assert len(topic_keywords[1]) == 5
        assert len(topic_keywords[2]) == 5
        
        # Проверяем ключевые слова для функций
        function_keywords = saved_keywords['labor_function']
        assert '3.1.1' in function_keywords
        assert '3.1.2' in function_keywords
        assert len(function_keywords['3.1.1']) == 5
        assert len(function_keywords['3.1.2']) == 5 