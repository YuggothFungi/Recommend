import unittest
import pickle
import numpy as np
from scipy import sparse
from src.db import get_db_connection
from src.tfidf_vectorizer import TextVectorizer

class TestVectorization(unittest.TestCase):
    def setUp(self):
        """Подготовка тестового окружения"""
        self.conn = get_db_connection()
        self.cursor = self.conn.cursor()
        self.vectorizer = TextVectorizer()
    
    def tearDown(self):
        """Очистка после тестов"""
        self.conn.close()
    
    def test_vectorizer_initialization(self):
        """Проверка инициализации векторизатора"""
        self.assertFalse(self.vectorizer.is_fitted, "Векторизатор не должен быть обучен при инициализации")
        self.assertIsNone(self.vectorizer.vector_size, "Размер вектора не должен быть определен при инициализации")
    
    def test_vectorizer_fit(self):
        """Проверка обучения векторизатора"""
        test_texts = [
            "тестовый текст первый",
            "тестовый текст второй",
            "еще один тестовый текст"
        ]
        
        self.vectorizer.fit(test_texts)
        self.assertTrue(self.vectorizer.is_fitted, "Векторизатор должен быть обучен после fit")
        self.assertIsNotNone(self.vectorizer.vector_size, "Размер вектора должен быть определен после fit")
    
    def test_vectors_exist(self):
        """Проверка наличия векторов в базе данных"""
        tables = ['topic_vectors', 'labor_function_vectors']
        
        for table in tables:
            self.cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = self.cursor.fetchone()[0]
            self.assertGreater(count, 0, f"Нет векторов в таблице {table}")
    
    def test_vector_format(self):
        """Проверка формата сохраненных векторов"""
        # Проверяем векторы тем
        self.cursor.execute("""
            SELECT tfidf_vector 
            FROM topic_vectors 
            LIMIT 1
        """)
        vector_bytes = self.cursor.fetchone()[0]
        vector = pickle.loads(vector_bytes)
        
        self.assertTrue(sparse.issparse(vector), "Вектор должен быть разреженной матрицей")
        self.assertEqual(vector.shape[0], 1, "Вектор должен быть одномерным")
        self.assertTrue(np.issubdtype(vector.dtype, np.float64), 
                       "Тип данных вектора должен быть float64")
    
    def test_vector_similarity(self):
        """Проверка косинусного сходства векторов"""
        # Получаем два вектора
        self.cursor.execute("""
            SELECT tfidf_vector 
            FROM topic_vectors 
            LIMIT 2
        """)
        vectors = [pickle.loads(row[0]) for row in self.cursor.fetchall()]
        
        if len(vectors) == 2:
            # Вычисляем косинусное сходство для разреженных матриц
            dot_product = vectors[0].dot(vectors[1].transpose()).toarray()[0, 0]
            norm1 = np.sqrt(vectors[0].dot(vectors[0].transpose()).toarray()[0, 0])
            norm2 = np.sqrt(vectors[1].dot(vectors[1].transpose()).toarray()[0, 0])
            similarity = dot_product / (norm1 * norm2) if norm1 * norm2 != 0 else 0
            
            self.assertGreaterEqual(similarity, 0, "Косинусное сходство не может быть отрицательным")
            self.assertLessEqual(similarity, 1, "Косинусное сходство не может быть больше 1")

if __name__ == '__main__':
    unittest.main() 