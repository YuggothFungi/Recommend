import unittest
import pytest
from src.db import get_db_connection

@pytest.mark.usefixtures("db_connection")
class TestDataLoading:
    """Тесты для проверки загрузки данных в базу данных"""
    
    def test_tables_exist(self, db_connection):
        """Проверка существования таблиц"""
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
        
        # Добавляем компетенции
        competencies_data = [
            ("C1", "Программирование", "Разработка программ", None, None, None),
            ("C2", "Веб-разработка", "Создание веб-сайтов", None, None, None),
            ("C3", "Анализ данных", "Машинное обучение", None, None, None)
        ]
        cursor.executemany(
            "INSERT INTO competencies (id, category, description, nltk_normalized_category, nltk_normalized_description, rubert_vector) VALUES (?, ?, ?, ?, ?, ?)",
            competencies_data
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
        
        # Связываем темы и компетенции
        topic_competency = [
            (1, "C1"),
            (2, "C2"),
            (3, "C3")
        ]
        cursor.executemany(
            "INSERT INTO topic_competency (topic_id, competency_id) VALUES (?, ?)",
            topic_competency
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
        
        tables = [
            "topics", "competencies", "labor_functions",
            "labor_components", "labor_function_components",
            "topic_competency"
        ]
        
        for table in tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            result = cursor.fetchone()
            assert result is not None, f"Таблица {table} не существует"
    
    def test_data_loaded(self, db_connection):
        """Проверка загрузки данных"""
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
        
        # Проверяем темы
        cursor.execute("SELECT COUNT(*) FROM topics")
        count = cursor.fetchone()[0]
        assert count > 0, "В таблице topics нет данных"
        
        # Проверяем трудовые функции
        cursor.execute("SELECT COUNT(*) FROM labor_functions")
        count = cursor.fetchone()[0]
        assert count > 0, "В таблице labor_functions нет данных"
    
    def test_relationships(self, db_connection):
        """Проверка связей между таблицами"""
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
        
        # Добавляем компетенции
        competencies_data = [
            ("C1", "Программирование", "Разработка программ", None, None, None),
            ("C2", "Веб-разработка", "Создание веб-сайтов", None, None, None),
            ("C3", "Анализ данных", "Машинное обучение", None, None, None)
        ]
        cursor.executemany(
            "INSERT INTO competencies (id, category, description, nltk_normalized_category, nltk_normalized_description, rubert_vector) VALUES (?, ?, ?, ?, ?, ?)",
            competencies_data
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
        
        # Связываем темы и компетенции
        topic_competency = [
            (1, "C1"),
            (2, "C2"),
            (3, "C3")
        ]
        cursor.executemany(
            "INSERT INTO topic_competency (topic_id, competency_id) VALUES (?, ?)",
            topic_competency
        )
        
        db_connection.commit()
        
        # Проверяем связи тем с компетенциями
        cursor.execute("""
            SELECT COUNT(*) 
            FROM topics t
            JOIN topic_competency tc ON t.id = tc.topic_id
            JOIN competencies c ON tc.competency_id = c.id
        """)
        count = cursor.fetchone()[0]
        assert count > 0, "Нет связей между темами и компетенциями"

if __name__ == '__main__':
    unittest.main() 