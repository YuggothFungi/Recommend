import unittest
from src.db import get_db_connection
from src.text_processor import TextProcessor

class TestTextProcessing(unittest.TestCase):
    def setUp(self):
        """Подготовка тестового окружения"""
        self.conn = get_db_connection()
        self.cursor = self.conn.cursor()
        self.processor = TextProcessor()
    
    def tearDown(self):
        """Очистка после тестов"""
        self.conn.close()
    
    def test_normalization(self):
        """Проверка нормализации текста"""
        test_cases = [
            ("Привет, мир!", "привет мир"),
            ("Python 3.8 и NLTK", "python nltk"),
            ("Это тестовый текст", "тестовый текст"),
            ("Стоп-слова должны быть удалены", "стоп слова должны удалены")
        ]
        
        for original, expected in test_cases:
            normalized = self.processor.normalize_text(original)
            self.assertEqual(normalized, expected, 
                           f"Нормализация текста '{original}' не соответствует ожидаемому результату")
    
    def test_normalized_columns_exist(self):
        """Проверка наличия колонок с нормализованным текстом"""
        tables_and_columns = [
            ('topics', ['nltk_normalized_title', 'nltk_normalized_description']),
            ('competencies', ['nltk_normalized_category', 'nltk_normalized_description']),
            ('labor_functions', ['nltk_normalized_name']),
            ('labor_components', ['nltk_normalized_description'])
        ]
        
        for table, columns in tables_and_columns:
            for column in columns:
                self.cursor.execute(f"""
                    SELECT COUNT(*) 
                    FROM pragma_table_info('{table}') 
                    WHERE name = ?
                """, (column,))
                self.assertTrue(self.cursor.fetchone()[0] > 0, 
                              f"Колонка {column} отсутствует в таблице {table}")
    
    def test_normalized_texts_not_empty(self):
        """Проверка наличия нормализованных текстов"""
        tables_and_columns = [
            ('topics', 'nltk_normalized_title'),
            ('competencies', 'nltk_normalized_description'),
            ('labor_functions', 'nltk_normalized_name'),
            ('labor_components', 'nltk_normalized_description')
        ]
        
        for table, column in tables_and_columns:
            self.cursor.execute(f"""
                SELECT COUNT(*) 
                FROM {table} 
                WHERE {column} IS NOT NULL AND {column} != ''
            """)
            count = self.cursor.fetchone()[0]
            self.assertGreater(count, 0, 
                             f"Нет нормализованных текстов в колонке {column} таблицы {table}")

if __name__ == '__main__':
    unittest.main() 