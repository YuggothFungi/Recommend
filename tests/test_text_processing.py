import unittest
import pytest
from src.text_processor import TextProcessor, DatabaseTextProcessor

@pytest.mark.usefixtures("db_connection")
class TestTextProcessing:
    """Тесты для обработки текста"""
    
    def test_normalization(self, db_connection):
        """Проверка нормализации текста"""
        cursor = db_connection.cursor()
        processor = TextProcessor()
        
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
        
        db_connection.commit()
        
        # Обрабатываем тексты
        db_processor = DatabaseTextProcessor()
        db_processor.process_topics(db_connection)
        db_processor.process_labor_functions(db_connection)
        
        # Получаем тестовые тексты
        cursor.execute("SELECT title, description FROM topics")
        texts = cursor.fetchall()
        
        for title, description in texts:
            normalized_title = processor.normalize_text(title)
            normalized_description = processor.normalize_text(description)
            
            # Проверяем, что нормализованный текст не пустой
            assert normalized_title is not None
            assert normalized_description is not None
            
            # Проверяем, что нормализованный текст отличается от исходного
            assert title != normalized_title
            assert description != normalized_description
    
    def test_normalized_columns_exist(self, db_connection):
        """Проверка существования колонок с нормализованным текстом"""
        cursor = db_connection.cursor()
        
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
        
        db_connection.commit()
        
        # Проверяем колонки в таблице topics
        cursor.execute("PRAGMA table_info(topics)")
        columns = [col[1] for col in cursor.fetchall()]
        assert "nltk_normalized_title" in columns
        assert "nltk_normalized_description" in columns
        
        # Проверяем колонки в таблице labor_functions
        cursor.execute("PRAGMA table_info(labor_functions)")
        columns = [col[1] for col in cursor.fetchall()]
        assert "nltk_normalized_name" in columns
    
    def test_normalized_texts_not_empty(self, db_connection):
        """Проверка, что нормализованные тексты не пустые"""
        cursor = db_connection.cursor()
        
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
        
        db_connection.commit()
        
        # Обрабатываем тексты
        processor = DatabaseTextProcessor()
        processor.process_topics(db_connection)
        processor.process_labor_functions(db_connection)
        
        # Проверяем темы
        cursor.execute("SELECT nltk_normalized_title, nltk_normalized_description FROM topics")
        texts = cursor.fetchall()
        for title, description in texts:
            assert title is not None
            assert description is not None
        
        # Проверяем трудовые функции
        cursor.execute("SELECT nltk_normalized_name FROM labor_functions")
        texts = cursor.fetchall()
        for name, in texts:
            assert name is not None

if __name__ == '__main__':
    unittest.main() 