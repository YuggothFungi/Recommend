import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
import pickle
import json
import os
from src.db import get_db_connection
from src.check_normalized_texts import check_normalized_texts

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
                COALESCE(lf.nltk_normalized_name, '')
            FROM labor_functions lf
        """)
        function_texts = cursor.fetchall()
        
        # Получаем компоненты для каждой функции
        result = []
        for function_id, function_text in function_texts:
            cursor.execute("""
                SELECT COALESCE(lc.nltk_normalized_description, '')
                FROM labor_function_components lfc
                JOIN labor_components lc ON lfc.component_id = lc.id
                WHERE lfc.labor_function_id = ?
            """, (function_id,))
            component_texts = cursor.fetchall()
            
            # Объединяем тексты компонентов
            component_text = ' '.join(text[0] for text in component_texts)
            
            # Объединяем с текстом функции
            full_text = f"{function_text} {component_text}".strip()
            result.append((function_id, full_text))
        
        return result
    
    def _save_vector(self, cursor, table_name, id_field, id_value, vector):
        """Сохранение вектора в базу данных"""
        # Проверяем существование колонки tfidf_vector
        cursor.execute(f"""
            SELECT COUNT(*) 
            FROM pragma_table_info('{table_name}') 
            WHERE name = 'tfidf_vector'
        """)
        if cursor.fetchone()[0] == 0:
            print(f"Добавляем колонку tfidf_vector в таблицу {table_name}")
            cursor.execute(f"""
                ALTER TABLE {table_name}
                ADD COLUMN tfidf_vector BLOB
            """)
        
        # Преобразуем sparse matrix в dense array
        if hasattr(vector, 'toarray'):
            vector = vector.toarray()
        
        # Преобразуем в float32 для совместимости с calculate_similarities
        vector = vector.astype(np.float32).reshape(-1)
        vector_bytes = vector.tobytes()
        
        print(f"Сохранение вектора для {id_field}={id_value} в таблице {table_name}")
        print(f"Размер вектора: {vector.shape}, тип: {vector.dtype}")
        
        # Проверяем, существует ли запись
        cursor.execute(f"""
            SELECT COUNT(*) 
            FROM {table_name} 
            WHERE {id_field} = ?
        """, (id_value,))
        exists = cursor.fetchone()[0] > 0
        
        if exists:
            # Обновляем существующую запись
            cursor.execute(f"""
                UPDATE {table_name}
                SET tfidf_vector = ?
                WHERE {id_field} = ?
            """, (vector_bytes, id_value))
        else:
            # Создаем новую запись
            cursor.execute(f"""
                INSERT INTO {table_name} ({id_field}, tfidf_vector)
                VALUES (?, ?)
            """, (id_value, vector_bytes))
        
        # Проверяем, что вектор сохранен
        cursor.execute(f"""
            SELECT tfidf_vector 
            FROM {table_name} 
            WHERE {id_field} = ?
        """, (id_value,))
        saved_vector = cursor.fetchone()
        if saved_vector and saved_vector[0]:
            saved_vector_array = np.frombuffer(saved_vector[0], dtype=np.float32)
            print(f"Вектор успешно сохранен для {id_field}={id_value}")
            print(f"Размер сохраненного вектора: {saved_vector_array.shape}")
            print(f"Сумма элементов: {np.sum(saved_vector_array)}")
            print(f"Количество ненулевых элементов: {np.count_nonzero(saved_vector_array)}")
        else:
            print(f"Ошибка: вектор не сохранен для {id_field}={id_value}")
    
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
            self._save_vector(cursor, 'topic_vectors', 'topic_id', topic_id, vector)
        
        # Векторизуем трудовые функции
        print("Векторизация трудовых функций...")
        function_texts_only = [text for _, text in function_texts]
        function_vectors = self.vectorizer.transform(function_texts_only)
        
        for (function_id, _), vector in zip(function_texts, function_vectors):
            self._save_vector(cursor, 'labor_function_vectors', 'labor_function_id', function_id, vector)
        
        conn.commit()
        
        if should_close:
            conn.close()
            
        print("Векторизация завершена!")

if __name__ == "__main__":
    vectorizer = DatabaseVectorizer()
    vectorizer.vectorize_all() 