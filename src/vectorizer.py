import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
import pickle
from db import get_db_connection

class TextVectorizer:
    def __init__(self):
        self.vectorizer = TfidfVectorizer()
        self.is_fitted = False
    
    def fit(self, texts):
        """Обучение векторизатора на текстах"""
        self.vectorizer.fit(texts)
        self.is_fitted = True
    
    def transform(self, texts):
        """Преобразование текстов в векторы"""
        if not self.is_fitted:
            raise ValueError("Векторизатор не обучен. Сначала вызовите метод fit().")
        return self.vectorizer.transform(texts)
    
    def fit_transform(self, texts):
        """Обучение и преобразование текстов в векторы"""
        return self.vectorizer.fit_transform(texts)

class DatabaseVectorizer:
    def __init__(self):
        self.vectorizer = TextVectorizer()
    
    def _get_topic_texts(self, cursor):
        """Получение объединенных нормализованных текстов тем"""
        cursor.execute("""
            SELECT 
                t.id,
                t.pymorphy2_nltk_normalized_title || ' ' || 
                COALESCE(t.pymorphy2_nltk_normalized_description, '')
            FROM topics t
        """)
        return cursor.fetchall()
    
    def _get_labor_function_texts(self, cursor):
        """Получение объединенных нормализованных текстов трудовых функций"""
        cursor.execute("""
            SELECT 
                lf.id,
                lf.pymorphy2_nltk_normalized_name || ' ' || 
                GROUP_CONCAT(lc.pymorphy2_nltk_normalized_description, ' ')
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
            INSERT OR REPLACE INTO {table_name} ({id_field}, vector)
            VALUES (?, ?)
        """, (id_value, vector_bytes))
    
    def vectorize_topics(self):
        """Векторизация тем"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Получаем тексты тем
        topic_texts = self._get_topic_texts(cursor)
        if not topic_texts:
            print("Нет тем для векторизации")
            return
        
        # Объединяем тексты для обучения векторизатора
        texts = [text for _, text in topic_texts]
        
        # Обучаем векторизатор и преобразуем тексты
        vectors = self.vectorizer.fit_transform(texts)
        
        # Сохраняем векторы
        for (topic_id, _), vector in zip(topic_texts, vectors):
            self._save_vector(cursor, 'topic_vectors', 'topic_id', topic_id, vector)
        
        conn.commit()
        conn.close()
        print("Векторизация тем завершена")
    
    def vectorize_labor_functions(self):
        """Векторизация трудовых функций"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Получаем тексты трудовых функций
        function_texts = self._get_labor_function_texts(cursor)
        if not function_texts:
            print("Нет трудовых функций для векторизации")
            return
        
        # Объединяем тексты для обучения векторизатора
        texts = [text for _, text in function_texts]
        
        # Обучаем векторизатор и преобразуем тексты
        vectors = self.vectorizer.fit_transform(texts)
        
        # Сохраняем векторы
        for (function_id, _), vector in zip(function_texts, vectors):
            self._save_vector(cursor, 'labor_function_vectors', 'labor_function_id', function_id, vector)
        
        conn.commit()
        conn.close()
        print("Векторизация трудовых функций завершена")
    
    def vectorize_all(self):
        """Векторизация всех текстов"""
        print("Векторизация тем...")
        self.vectorize_topics()
        
        print("Векторизация трудовых функций...")
        self.vectorize_labor_functions()
        
        print("Векторизация завершена!")

if __name__ == "__main__":
    vectorizer = DatabaseVectorizer()
    vectorizer.vectorize_all() 