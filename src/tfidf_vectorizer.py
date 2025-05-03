import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
import pickle
import json
import os
from src.db import get_db_connection

class TextVectorizer:
    def __init__(self):
        self.vectorizer = TfidfVectorizer()
        self.is_fitted = False
        self.vector_size = None
    
    def fit(self, texts):
        """Обучение векторизатора на текстах"""
        # Заменяем None на пустую строку
        texts = [text if text is not None else "" for text in texts]
        self.vectorizer.fit(texts)
        self.is_fitted = True
        # Получаем размер вектора после обучения
        test_vector = self.vectorizer.transform(['test'])
        self.vector_size = test_vector.shape[1]
    
    def transform(self, texts):
        """Преобразование текстов в векторы"""
        if not self.is_fitted:
            raise ValueError("Векторизатор не обучен. Сначала вызовите метод fit().")
        # Заменяем None на пустую строку
        texts = [text if text is not None else "" for text in texts]
        return self.vectorizer.transform(texts)
    
    def fit_transform(self, texts):
        """Обучение и преобразование текстов в векторы"""
        # Заменяем None на пустую строку
        texts = [text if text is not None else "" for text in texts]
        result = self.vectorizer.fit_transform(texts)
        # Получаем размер вектора после обучения
        self.vector_size = result.shape[1]
        return result

class DatabaseVectorizer:
    def __init__(self):
        self.vectorizer = TextVectorizer()
        self.meta_file = 'data/vectorizer_meta.json'
    
    def _save_meta(self):
        """Сохранение метаданных векторизатора"""
        meta = {
            'vector_size': self.vectorizer.vector_size,
            'vocabulary_size': len(self.vectorizer.vectorizer.vocabulary_)
        }
        os.makedirs(os.path.dirname(self.meta_file), exist_ok=True)
        with open(self.meta_file, 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
    
    def _get_topic_texts(self, cursor):
        """Получение объединенных нормализованных текстов тем"""
        cursor.execute("""
            SELECT 
                t.id,
                COALESCE(t.nltk_normalized_title, '') || ' ' || 
                COALESCE(t.nltk_normalized_description, '')
            FROM topics t
        """)
        return cursor.fetchall()
    
    def _get_labor_function_texts(self, cursor):
        """Получение объединенных нормализованных текстов трудовых функций"""
        cursor.execute("""
            SELECT 
                lf.id,
                COALESCE(lf.nltk_normalized_name, '') || ' ' || 
                GROUP_CONCAT(COALESCE(lc.nltk_normalized_description, ''), ' ')
            FROM labor_functions lf
            LEFT JOIN labor_function_components lfc ON lf.id = lfc.labor_function_id
            LEFT JOIN labor_components lc ON lfc.component_id = lc.id
            GROUP BY lf.id
        """)
        return cursor.fetchall()
    
    def _save_vector(self, cursor, table_name, id_field, id_value, vector):
        """Сохранение вектора в базу данных"""
        vector_bytes = pickle.dumps(vector)
        cursor.execute(f"""
            INSERT OR REPLACE INTO {table_name} ({id_field}, tfidf_vector)
            VALUES (?, ?)
        """, (id_value, vector_bytes))
    
    def vectorize_all(self):
        """Векторизация всех текстов"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Получаем все тексты
        topic_texts = self._get_topic_texts(cursor)
        function_texts = self._get_labor_function_texts(cursor)
        
        if not topic_texts or not function_texts:
            print("Нет текстов для векторизации")
            return
        
        # Объединяем все тексты для обучения векторизатора
        all_texts = [text for _, text in topic_texts + function_texts]
        
        # Обучаем векторизатор
        print("Обучение векторизатора...")
        self.vectorizer.fit(all_texts)
        
        # Сохраняем метаданные
        self._save_meta()
        print(f"Размер вектора: {self.vectorizer.vector_size}")
        
        # Векторизуем темы
        print("Векторизация тем...")
        topic_texts_only = [text for _, text in topic_texts]
        topic_vectors = self.vectorizer.transform(topic_texts_only)
        
        for (topic_id, _), vector in zip(topic_texts, topic_vectors):
            self._save_vector(cursor, 'topic_vectors', 'topic_id', topic_id, vector)
        
        # Векторизуем трудовые функции
        print("Векторизация трудовых функций...")
        function_texts_only = [text for _, text in function_texts]
        function_vectors = self.vectorizer.transform(function_texts_only)
        
        for (function_id, _), vector in zip(function_texts, function_vectors):
            self._save_vector(cursor, 'labor_function_vectors', 'labor_function_id', function_id, vector)
        
        conn.commit()
        conn.close()
        print("Векторизация завершена!")

if __name__ == "__main__":
    vectorizer = DatabaseVectorizer()
    vectorizer.vectorize_all() 