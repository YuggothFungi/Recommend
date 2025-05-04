from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import json
import os
from src.tfidf_vectorizer import DatabaseVectorizer as TfidfDatabaseVectorizer
from src.rubert_vectorizer import RuBertVectorizer
import pickle
import numpy as np
from src.db import get_db_connection

class BaseVectorizer(ABC):
    """Абстрактный базовый класс для векторизаторов"""
    
    @abstractmethod
    def fit(self, texts: List[str]) -> None:
        """Обучение векторизатора на текстах"""
        pass
    
    @abstractmethod
    def transform(self, texts: List[str]) -> Any:
        """Преобразование текстов в векторы"""
        pass
    
    @abstractmethod
    def fit_transform(self, texts: List[str]) -> Any:
        """Обучение и преобразование текстов в векторы"""
        pass
    
    @abstractmethod
    def save_meta(self, meta_file: str) -> None:
        """Сохранение метаданных векторизатора"""
        pass
    
    @abstractmethod
    def load_meta(self, meta_file: str) -> Dict[str, Any]:
        """Загрузка метаданных векторизатора"""
        pass

class DatabaseVectorizer:
    """Обёртка для работы с векторизаторами в базе данных"""
    
    def __init__(self, vectorizer_type: str = "tfidf"):
        """
        Инициализация векторизатора
        
        Args:
            vectorizer_type: Тип векторизатора ("tfidf", "rubert")
        """
        self.vectorizer_type = vectorizer_type
        self.meta_file = 'data/vectorizer_meta.json'
        
        # Выбор конкретной реализации векторизатора
        if vectorizer_type == "tfidf":
            self.vectorizer = TfidfDatabaseVectorizer()
        elif vectorizer_type == "rubert":
            self.vectorizer = RuBertVectorizer()
        else:
            raise ValueError(f"Неизвестный тип векторизатора: {vectorizer_type}")
    
    def vectorize_all(self) -> None:
        """Векторизация всех текстов"""
        self.vectorizer.vectorize_all()
    
    def get_meta(self) -> Dict[str, Any]:
        """Получение метаданных векторизатора"""
        if os.path.exists(self.meta_file):
            with open(self.meta_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def save_meta(self) -> None:
        """Сохранение метаданных векторизатора"""
        self.vectorizer._save_meta()

def calculate_similarities(conn=None):
    """Расчет сходства между темами и трудовыми функциями"""
    if conn is None:
        conn = get_db_connection()
        should_close = True
    else:
        should_close = False
        
    cursor = conn.cursor()
    
    # Получаем все вектора тем
    cursor.execute("""
        SELECT topic_id, tfidf_vector, rubert_vector
        FROM topic_vectors
    """)
    topic_vectors = cursor.fetchall()
    
    # Получаем все вектора трудовых функций
    cursor.execute("""
        SELECT labor_function_id, tfidf_vector, rubert_vector
        FROM labor_function_vectors
    """)
    function_vectors = cursor.fetchall()
    
    # Для каждой пары считаем сходство
    for topic_id, topic_tfidf, topic_rubert in topic_vectors:
        for function_id, function_tfidf, function_rubert in function_vectors:
            # Сходство по TF-IDF
            if topic_tfidf and function_tfidf:
                topic_tfidf_vec = pickle.loads(topic_tfidf)
                function_tfidf_vec = pickle.loads(function_tfidf)
                tfidf_sim = np.dot(topic_tfidf_vec, function_tfidf_vec.T).toarray()[0][0]
            else:
                tfidf_sim = 0.0
            
            # Сходство по ruBERT
            if topic_rubert and function_rubert:
                topic_rubert_vec = np.frombuffer(topic_rubert, dtype=np.float32)
                function_rubert_vec = np.frombuffer(function_rubert, dtype=np.float32)
                rubert_sim = float(np.dot(topic_rubert_vec, function_rubert_vec) / (
                    np.linalg.norm(topic_rubert_vec) * np.linalg.norm(function_rubert_vec)
                ))
            else:
                rubert_sim = 0.0
            
            # Сохраняем сходство
            cursor.execute("""
                INSERT OR REPLACE INTO topic_labor_function 
                (topic_id, labor_function_id, tfidf_similarity, rubert_similarity)
                VALUES (?, ?, ?, ?)
            """, (topic_id, function_id, float(tfidf_sim), float(rubert_sim)))
    
    conn.commit()
    
    if should_close:
        conn.close()