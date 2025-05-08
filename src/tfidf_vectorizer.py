import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
import pickle
import json
import os
from src.db import get_db_connection
from src.check_normalized_texts import check_normalized_texts
from src.vectorization_config import VectorizationConfig
from src.vectorization_text_weights import VectorizationTextWeights

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

class TfidfDatabaseVectorizer:
    """Векторизатор TF-IDF для работы с базой данных"""
    
    def __init__(self, config: VectorizationConfig = None):
        """
        Инициализация векторизатора
        
        Args:
            config: Конфигурация векторизации
        """
        self.vectorizer = TextVectorizer()
        self.meta_file = 'data/vectorizer_meta.json'
        self.config = config
        self.text_weights = VectorizationTextWeights(config)
    
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
        cursor.execute("SELECT id FROM lecture_topics")
        lecture_topics = cursor.fetchall()
        
        cursor.execute("SELECT id FROM practical_topics")
        practical_topics = cursor.fetchall()
        
        result = []
        for topic_id, in lecture_topics:
            text, _ = self.text_weights.get_lecture_topic_text(topic_id, cursor.connection)
            result.append((topic_id, text))
        
        for topic_id, in practical_topics:
            text, _ = self.text_weights.get_practical_topic_text(topic_id, cursor.connection)
            result.append((topic_id, text))
        
        return result
    
    def _get_labor_function_texts(self, cursor):
        """Получение объединенных нормализованных текстов трудовых функций"""
        cursor.execute("SELECT id FROM labor_functions")
        labor_functions = cursor.fetchall()
        
        result = []
        for function_id, in labor_functions:
            text = self.text_weights.get_labor_function_text(function_id, cursor.connection)
            result.append((function_id, text))
        
        return result
    
    def _save_vector(self, cursor, entity_type: str, entity_id: int, vector):
        """Сохранение вектора в базу данных"""
        # Преобразуем sparse matrix в dense array
        if hasattr(vector, 'toarray'):
            vector = vector.toarray()
        
        # Преобразуем в float32
        vector = vector.astype(np.float32).reshape(-1)
        vector_bytes = vector.tobytes()
        
        # Сохраняем в vectorization_results
        cursor.execute("""
            INSERT INTO vectorization_results 
            (configuration_id, entity_type, entity_id, vector_type, vector_data)
            VALUES (?, ?, ?, ?, ?)
        """, (
            self.config.config_id,
            entity_type,
            entity_id,
            'tfidf',
            vector_bytes
        ))
    
    def vectorize_all(self, conn=None):
        """Векторизация всех текстов"""
        if conn is None:
            conn = get_db_connection()
            should_close = True
        else:
            should_close = False
            
        # Проверяем нормализованные тексты
        check_normalized_texts(conn)
            
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
            self._save_vector(cursor, 'lecture_topic' if topic_id in [t[0] for t in topic_texts[:len(topic_texts)//2]] else 'practical_topic', topic_id, vector)
        
        # Векторизуем трудовые функции
        print("Векторизация трудовых функций...")
        function_texts_only = [text for _, text in function_texts]
        function_vectors = self.vectorizer.transform(function_texts_only)
        
        for (function_id, _), vector in zip(function_texts, function_vectors):
            self._save_vector(cursor, 'labor_function', function_id, vector)
        
        conn.commit()
        
        if should_close:
            conn.close()
            
        print("Векторизация завершена!")

    def fit(self, texts):
        """Обучение векторизатора на текстах"""
        return self.vectorizer.fit(texts)

    def transform(self, texts):
        """Преобразование текстов в векторы"""
        if not self.vectorizer.is_fitted:
            raise ValueError("Векторизатор не обучен. Сначала вызовите метод fit()")
        return self.vectorizer.transform(texts)

    def fit_transform(self, texts):
        """Обучение и преобразование текстов в векторы"""
        return self.vectorizer.fit_transform(texts)

if __name__ == "__main__":
    vectorizer = TfidfDatabaseVectorizer()
    vectorizer.vectorize_all() 