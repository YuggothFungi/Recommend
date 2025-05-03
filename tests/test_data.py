import unittest
from src.db import get_db_connection

class TestDataLoading(unittest.TestCase):
    def setUp(self):
        """Подготовка тестового окружения"""
        self.conn = get_db_connection()
        self.cursor = self.conn.cursor()
    
    def tearDown(self):
        """Очистка после тестов"""
        self.conn.close()
    
    def test_tables_exist(self):
        """Проверка существования всех необходимых таблиц"""
        required_tables = [
            'topics',
            'competencies',
            'labor_functions',
            'component_types',
            'labor_components',
            'labor_function_components',
            'topic_competency',
            'topic_labor_function'
        ]
        
        for table in required_tables:
            self.cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            self.assertTrue(self.cursor.fetchone(), f"Таблица {table} не существует")
    
    def test_data_loaded(self):
        """Проверка наличия данных в таблицах"""
        tables = [
            'topics',
            'competencies',
            'labor_functions',
            'component_types',
            'labor_components'
        ]
        
        for table in tables:
            self.cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = self.cursor.fetchone()[0]
            self.assertGreater(count, 0, f"Таблица {table} пуста")
    
    def test_relationships(self):
        """Проверка связей между таблицами"""
        # Проверка связей тем и компетенций
        self.cursor.execute("""
            SELECT COUNT(*) 
            FROM topic_competency tc
            JOIN topics t ON tc.topic_id = t.id
            JOIN competencies c ON tc.competency_id = c.id
        """)
        count = self.cursor.fetchone()[0]
        self.assertGreater(count, 0, "Нет связей между темами и компетенциями")
        
        # Проверка связей трудовых функций и компонентов
        self.cursor.execute("""
            SELECT COUNT(*) 
            FROM labor_function_components lfc
            JOIN labor_functions lf ON lfc.labor_function_id = lf.id
            JOIN labor_components lc ON lfc.component_id = lc.id
        """)
        count = self.cursor.fetchone()[0]
        self.assertGreater(count, 0, "Нет связей между трудовыми функциями и компонентами")

if __name__ == '__main__':
    unittest.main() 