import torch
from transformers import AutoTokenizer, AutoModel
from typing import List, Dict, Any
import numpy as np
import json
import os
import sqlite3
from src.db import get_db_connection
from src.check_normalized_texts import check_normalized_texts

class RuBertVectorizer:
    """Векторизатор на основе ruBERT"""
    
    def __init__(self, conn=None):
        """Инициализация векторизатора"""
        self.model_name = 'sberbank-ai/sbert_large_nlu_ru'
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModel.from_pretrained(self.model_name)
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model.to(self.device)
        self.model.eval()
        self.vector_size = 1024  # Размер вектора для sbert_large_nlu_ru
        self.db_conn = conn  # Использовать переданное соединение
    
    def _mean_pooling(self, model_output, attention_mask):
        """Усреднение токенов для получения эмбеддинга предложения"""
        token_embeddings = model_output[0]
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)
    
    def fit(self, texts: List[str]) -> None:
        """Обучение векторизатора (не требуется для BERT)"""
        pass
    
    def transform(self, texts: List[str]) -> np.ndarray:
        """Преобразование текстов в векторы"""
        if not texts:
            return np.array([])
        
        # Токенизация
        encoded_input = self.tokenizer(texts, padding=True, truncation=True, max_length=512, return_tensors='pt')
        encoded_input = {k: v.to(self.device) for k, v in encoded_input.items()}
        
        # Получение эмбеддингов
        with torch.no_grad():
            model_output = self.model(**encoded_input)
        
        # Усреднение токенов
        sentence_embeddings = self._mean_pooling(model_output, encoded_input['attention_mask'])
        
        # Нормализация векторов
        sentence_embeddings = torch.nn.functional.normalize(sentence_embeddings, p=2, dim=1)
        
        # Преобразование в numpy
        return sentence_embeddings.cpu().numpy()
    
    def fit_transform(self, texts: List[str]) -> np.ndarray:
        """Обучение и преобразование текстов в векторы"""
        return self.transform(texts)
    
    def save_meta(self, meta_file: str) -> None:
        """Сохранение метаданных векторизатора"""
        meta = {
            'model_name': self.model_name,
            'vector_size': self.vector_size
        }
        os.makedirs(os.path.dirname(meta_file), exist_ok=True)
        with open(meta_file, 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
    
    def load_meta(self, meta_file: str) -> Dict[str, Any]:
        """Загрузка метаданных векторизатора"""
        if os.path.exists(meta_file):
            with open(meta_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
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
    
    def _vectorize_table(self, table_name: str, text_column: str, conn=None) -> None:
        """Векторизация текстов в таблице"""
        if conn is None:
            conn = self.db_conn
        if conn is None:
            raise ValueError("Не указано соединение с базой данных")
            
        cursor = conn.cursor()
        
        # Проверяем наличие столбца rubert_vector
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        has_vector_column = any(col[1] == 'rubert_vector' for col in columns)
        
        if not has_vector_column:
            cursor.execute(f"""
                ALTER TABLE {table_name}
                ADD COLUMN rubert_vector BLOB
            """)
        
        # Получаем тексты
        cursor.execute(f"SELECT id, {text_column} FROM {table_name}")
        texts = cursor.fetchall()
        
        if not texts:
            return
        
        # Векторизуем тексты
        text_ids = [row[0] for row in texts]
        text_contents = [row[1] for row in texts]
        vectors = self.transform(text_contents)
        
        # Сохраняем векторы
        for text_id, vector in zip(text_ids, vectors):
            vector_bytes = vector.tobytes()
            cursor.execute(f"""
                UPDATE {table_name}
                SET rubert_vector = ?
                WHERE id = ?
            """, (vector_bytes, text_id))
        
        conn.commit()
    
    def vectorize_all(self, conn=None) -> None:
        """Векторизация всех текстов в базе данных"""
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
        
        # Векторизуем темы
        print("Векторизация тем...")
        topic_texts_only = [text for _, text in topic_texts]
        topic_vectors = self.transform(topic_texts_only)
        
        for (topic_id, _), vector in zip(topic_texts, topic_vectors):
            vector_bytes = vector.tobytes()
            # Проверяем существование записи
            cursor.execute("""
                SELECT COUNT(*) FROM topic_vectors WHERE topic_id = ?
            """, (topic_id,))
            exists = cursor.fetchone()[0] > 0
            
            if exists:
                cursor.execute("""
                    UPDATE topic_vectors
                    SET rubert_vector = ?
                    WHERE topic_id = ?
                """, (vector_bytes, topic_id))
            else:
                cursor.execute("""
                    INSERT INTO topic_vectors (topic_id, rubert_vector)
                    VALUES (?, ?)
                """, (topic_id, vector_bytes))
        
        # Векторизуем трудовые функции
        print("Векторизация трудовых функций...")
        function_texts_only = [text for _, text in function_texts]
        function_vectors = self.transform(function_texts_only)
        
        for (function_id, _), vector in zip(function_texts, function_vectors):
            vector_bytes = vector.tobytes()
            # Проверяем существование записи
            cursor.execute("""
                SELECT COUNT(*) FROM labor_function_vectors WHERE labor_function_id = ?
            """, (function_id,))
            exists = cursor.fetchone()[0] > 0
            
            if exists:
                cursor.execute("""
                    UPDATE labor_function_vectors
                    SET rubert_vector = ?
                    WHERE labor_function_id = ?
                """, (vector_bytes, function_id))
            else:
                cursor.execute("""
                    INSERT INTO labor_function_vectors (labor_function_id, rubert_vector)
                    VALUES (?, ?)
                """, (function_id, vector_bytes))
        
        conn.commit()
        
        if should_close:
            conn.close()
    
    def get_vector(self, text: str) -> np.ndarray:
        """Получение вектора для текста"""
        return self.transform([text])[0]
    
    def get_similarity(self, text1: str, text2: str) -> float:
        """Вычисление косинусного сходства между текстами"""
        vec1 = self.get_vector(text1)
        vec2 = self.get_vector(text2)
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)) 