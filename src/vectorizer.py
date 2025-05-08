from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import json
import os
from src.tfidf_vectorizer import TfidfDatabaseVectorizer
from src.rubert_vectorizer import RuBertVectorizer
import pickle
import numpy as np
from src.db import get_db_connection
from src.vectorization_config import VectorizationConfig
from src.vectorization_text_weights import VectorizationTextWeights

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

class Vectorizer:
    """Обёртка для работы с векторизаторами в базе данных"""
    
    def __init__(self, config: Optional[VectorizationConfig] = None, vectorizer_type: str = "tfidf"):
        """
        Инициализация векторизатора
        
        Args:
            config: Конфигурация векторизации
            vectorizer_type: Тип векторизатора ("tfidf", "rubert")
        """
        self.vectorizer_type = vectorizer_type
        self.meta_file = 'data/vectorizer_meta.json'
        self.config = config
        
        # Выбор конкретной реализации векторизатора
        if vectorizer_type == "tfidf":
            self.vectorizer = TfidfDatabaseVectorizer(config)
        elif vectorizer_type == "rubert":
            self.vectorizer = RuBertVectorizer(config)
        else:
            raise ValueError(f"Неизвестный тип векторизатора: {vectorizer_type}")
        
        # Инициализация обработчика весов текста
        if config is not None:
            self.text_weights = VectorizationTextWeights(config)
    
    def vectorize_all(self, conn=None) -> None:
        """Векторизация всех текстов"""
        if self.config is None:
            # Используем старый метод векторизации
            self.vectorizer.vectorize_all(conn)
            return
            
        if conn is None:
            conn = get_db_connection()
            should_close = True
        else:
            should_close = False
            
        cursor = conn.cursor()
        
        # Собираем все тексты для обучения
        all_texts = []
        
        # Получаем тексты тем лекций
        cursor.execute("SELECT id FROM lecture_topics")
        lecture_topics = cursor.fetchall()
        for topic_id, in lecture_topics:
            text, _ = self.text_weights.get_lecture_topic_text(topic_id, conn)
            all_texts.append(text)
        
        # Получаем тексты тем практик
        cursor.execute("SELECT id FROM practical_topics")
        practical_topics = cursor.fetchall()
        for topic_id, in practical_topics:
            text, _ = self.text_weights.get_practical_topic_text(topic_id, conn)
            all_texts.append(text)
        
        # Получаем тексты трудовых функций
        cursor.execute("SELECT id FROM labor_functions")
        labor_functions = cursor.fetchall()
        for function_id, in labor_functions:
            text = self.text_weights.get_labor_function_text(function_id, conn)
            all_texts.append(text)
        
        # Обучаем векторизатор на всех текстах
        print("Обучение векторизатора...")
        self.vectorizer.fit(all_texts)
        print("Векторизатор обучен")
        
        # Векторизуем темы лекций
        print("Векторизация тем лекций...")
        for topic_id, in lecture_topics:
            text, hours = self.text_weights.get_lecture_topic_text(topic_id, conn)
            vector = self.vectorizer.transform([text])[0]
            
            # Преобразуем разреженную матрицу в плотную перед сохранением
            if hasattr(vector, 'toarray'):
                vector = vector.toarray()
            
            # Сохраняем результат
            cursor.execute("""
                INSERT INTO vectorization_results 
                (configuration_id, entity_type, entity_id, vector_type, vector_data)
                VALUES (?, ?, ?, ?, ?)
            """, (
                self.config.config_id,
                'lecture_topic',
                topic_id,
                self.vectorizer_type,
                vector.tobytes()
            ))
        
        # Векторизуем темы практик
        print("Векторизация тем практик...")
        for topic_id, in practical_topics:
            text, hours = self.text_weights.get_practical_topic_text(topic_id, conn)
            vector = self.vectorizer.transform([text])[0]
            
            # Преобразуем разреженную матрицу в плотную перед сохранением
            if hasattr(vector, 'toarray'):
                vector = vector.toarray()
            
            # Сохраняем результат
            cursor.execute("""
                INSERT INTO vectorization_results 
                (configuration_id, entity_type, entity_id, vector_type, vector_data)
                VALUES (?, ?, ?, ?, ?)
            """, (
                self.config.config_id,
                'practical_topic',
                topic_id,
                self.vectorizer_type,
                vector.tobytes()
            ))
        
        # Векторизуем трудовые функции
        print("Векторизация трудовых функций...")
        for function_id, in labor_functions:
            text = self.text_weights.get_labor_function_text(function_id, conn)
            vector = self.vectorizer.transform([text])[0]
            
            # Преобразуем разреженную матрицу в плотную перед сохранением
            if hasattr(vector, 'toarray'):
                vector = vector.toarray()
            
            # Сохраняем результат
            cursor.execute("""
                INSERT INTO vectorization_results 
                (configuration_id, entity_type, entity_id, vector_type, vector_data)
                VALUES (?, ?, ?, ?, ?)
            """, (
                self.config.config_id,
                'labor_function',
                function_id,
                self.vectorizer_type,
                vector.tobytes()
            ))
        
        conn.commit()
        
        if should_close:
            conn.close()
            
        print("Векторизация завершена!")
    
    def get_meta(self) -> Dict[str, Any]:
        """Получение метаданных векторизатора"""
        if os.path.exists(self.meta_file):
            with open(self.meta_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def save_meta(self) -> None:
        """Сохранение метаданных векторизатора"""
        self.vectorizer._save_meta()

def calculate_similarities(config: VectorizationConfig):
    """
    Рассчитывает сходство между темами и трудовыми функциями
    
    Args:
        config: Конфигурация векторизации
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Получаем все векторы тем лекций
    cursor.execute("""
        SELECT entity_id, vector_data, vector_type
        FROM vectorization_results
        WHERE configuration_id = ? AND entity_type = 'lecture_topic'
    """, (config.config_id,))
    lecture_vectors = cursor.fetchall()
    
    # Получаем все векторы тем практик
    cursor.execute("""
        SELECT entity_id, vector_data, vector_type
        FROM vectorization_results
        WHERE configuration_id = ? AND entity_type = 'practical_topic'
    """, (config.config_id,))
    practical_vectors = cursor.fetchall()
    
    # Получаем все векторы трудовых функций
    cursor.execute("""
        SELECT entity_id, vector_data, vector_type
        FROM vectorization_results
        WHERE configuration_id = ? AND entity_type = 'labor_function'
    """, (config.config_id,))
    function_vectors = cursor.fetchall()
    
    # Группируем векторы по типу
    lecture_vectors_by_type = {}
    practical_vectors_by_type = {}
    function_vectors_by_type = {}
    
    for topic_id, vector_data, vector_type in lecture_vectors:
        if vector_type not in lecture_vectors_by_type:
            lecture_vectors_by_type[vector_type] = []
        lecture_vectors_by_type[vector_type].append((topic_id, np.frombuffer(vector_data)))
    
    for topic_id, vector_data, vector_type in practical_vectors:
        if vector_type not in practical_vectors_by_type:
            practical_vectors_by_type[vector_type] = []
        practical_vectors_by_type[vector_type].append((topic_id, np.frombuffer(vector_data)))
    
    for function_id, vector_data, vector_type in function_vectors:
        if vector_type not in function_vectors_by_type:
            function_vectors_by_type[vector_type] = []
        function_vectors_by_type[vector_type].append((function_id, np.frombuffer(vector_data)))
    
    # Получаем часы для тем
    cursor.execute("SELECT id, hours FROM lecture_topics")
    lecture_hours = {row[0]: row[1] for row in cursor.fetchall()}
    
    cursor.execute("SELECT id, hours FROM practical_topics")
    practical_hours = {row[0]: row[1] for row in cursor.fetchall()}
    
    # Рассчитываем сходство для каждого типа векторов
    for vector_type in ['tfidf', 'rubert']:
        # Для лекционных тем
        if vector_type in lecture_vectors_by_type and vector_type in function_vectors_by_type:
            for topic_id, topic_vec in lecture_vectors_by_type[vector_type]:
                for function_id, function_vec in function_vectors_by_type[vector_type]:
                    # Для TF-IDF нормализуем векторы, для RuBERT они уже нормализованы
                    if vector_type == 'tfidf':
                        topic_vec_norm = topic_vec / np.linalg.norm(topic_vec)
                        function_vec_norm = function_vec / np.linalg.norm(function_vec)
                    else:
                        topic_vec_norm = topic_vec
                        function_vec_norm = function_vec
                    
                    # Считаем косинусное сходство
                    similarity = float(np.dot(topic_vec_norm, function_vec_norm))
                    
                    # Сохраняем результат
                    cursor.execute("""
                        INSERT INTO similarity_results 
                        (configuration_id, topic_id, topic_type, labor_function_id, 
                         rubert_similarity, tfidf_similarity, topic_hours)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        config.config_id,
                        topic_id,
                        'lecture',
                        function_id,
                        similarity if vector_type == 'rubert' else 0.0,  # rubert_similarity
                        similarity if vector_type == 'tfidf' else 0.0,  # tfidf_similarity
                        lecture_hours.get(topic_id, 0)
                    ))
        
        # Для практических тем
        if vector_type in practical_vectors_by_type and vector_type in function_vectors_by_type:
            for topic_id, topic_vec in practical_vectors_by_type[vector_type]:
                for function_id, function_vec in function_vectors_by_type[vector_type]:
                    # Для TF-IDF нормализуем векторы, для RuBERT они уже нормализованы
                    if vector_type == 'tfidf':
                        topic_vec_norm = topic_vec / np.linalg.norm(topic_vec)
                        function_vec_norm = function_vec / np.linalg.norm(function_vec)
                    else:
                        topic_vec_norm = topic_vec
                        function_vec_norm = function_vec
                    
                    # Считаем косинусное сходство
                    similarity = float(np.dot(topic_vec_norm, function_vec_norm))
                    
                    # Сохраняем результат
                    cursor.execute("""
                        INSERT INTO similarity_results 
                        (configuration_id, topic_id, topic_type, labor_function_id, 
                         rubert_similarity, tfidf_similarity, topic_hours)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        config.config_id,
                        topic_id,
                        'practical',
                        function_id,
                        similarity if vector_type == 'rubert' else 0.0,  # rubert_similarity
                        similarity if vector_type == 'tfidf' else 0.0,  # tfidf_similarity
                        practical_hours.get(topic_id, 0)
                    ))
    
    conn.commit()
    conn.close()