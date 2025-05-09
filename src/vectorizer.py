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
import sqlite3

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
            self.vectorizer = RuBertVectorizer(config=config)
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
    """Расчет схожести между векторами"""
    print("\n=== Начало расчета схожести ===")
    
    # Загрузка векторов
    lecture_vectors = {}
    practical_vectors = {}
    labor_vectors = {}
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Загрузка векторов лекций
        cursor.execute("""
            SELECT entity_id, vector_data 
            FROM vectorization_results 
            WHERE configuration_id = ? AND entity_type = 'lecture_topic' AND vector_type = 'rubert'
        """, (config.config_id,))
        
        for entity_id, vector_bytes in cursor.fetchall():
            try:
                vector = np.frombuffer(vector_bytes, dtype=np.float32)
                norm = np.linalg.norm(vector)
                print(f"Лекция {entity_id}: норма = {norm}")
                if not np.isclose(norm, 1.0, rtol=1e-5):
                    print(f"Warning: Lecture vector {entity_id} is not normalized. Norm: {norm}")
                    vector = vector / norm
                lecture_vectors[entity_id] = vector
            except Exception as e:
                print(f"Error loading lecture vector {entity_id}: {str(e)}")
        
        # Загрузка векторов практик
        cursor.execute("""
            SELECT entity_id, vector_data 
            FROM vectorization_results 
            WHERE configuration_id = ? AND entity_type = 'practical_topic' AND vector_type = 'rubert'
        """, (config.config_id,))
        
        for entity_id, vector_bytes in cursor.fetchall():
            try:
                vector = np.frombuffer(vector_bytes, dtype=np.float32)
                norm = np.linalg.norm(vector)
                print(f"Практика {entity_id}: норма = {norm}")
                if not np.isclose(norm, 1.0, rtol=1e-5):
                    print(f"Warning: Practical vector {entity_id} is not normalized. Norm: {norm}")
                    vector = vector / norm
                practical_vectors[entity_id] = vector
            except Exception as e:
                print(f"Error loading practical vector {entity_id}: {str(e)}")
        
        # Загрузка векторов трудовых функций
        cursor.execute("""
            SELECT entity_id, vector_data 
            FROM vectorization_results 
            WHERE configuration_id = ? AND entity_type = 'labor_function' AND vector_type = 'rubert'
        """, (config.config_id,))
        
        for entity_id, vector_bytes in cursor.fetchall():
            try:
                vector = np.frombuffer(vector_bytes, dtype=np.float32)
                norm = np.linalg.norm(vector)
                print(f"Трудовая функция {entity_id}: норма = {norm}")
                if not np.isclose(norm, 1.0, rtol=1e-5):
                    print(f"Warning: Labor function vector {entity_id} is not normalized. Norm: {norm}")
                    vector = vector / norm
                labor_vectors[entity_id] = vector
            except Exception as e:
                print(f"Error loading labor function vector {entity_id}: {str(e)}")
        
        # Расчет схожести
        print("\nРасчет схожести...")
        
        # Для лекций
        for topic_id, topic_vector in lecture_vectors.items():
            for function_id, function_vector in labor_vectors.items():
                similarity = np.dot(topic_vector, function_vector)
                print(f"Лекция {topic_id} - Трудовая функция {function_id}: {similarity}")
                
                # Сохраняем результат
                cursor.execute("""
                    INSERT INTO similarity_results 
                    (configuration_id, topic_id, topic_type, labor_function_id, rubert_similarity, tfidf_similarity, topic_hours)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    config.config_id,
                    topic_id,
                    'lecture',
                    function_id,
                    float(similarity),
                    0.0,  # TF-IDF схожесть пока не рассчитываем
                    0.0   # Часы пока не учитываем
                ))
        
        # Для практик
        for topic_id, topic_vector in practical_vectors.items():
            for function_id, function_vector in labor_vectors.items():
                similarity = np.dot(topic_vector, function_vector)
                print(f"Практика {topic_id} - Трудовая функция {function_id}: {similarity}")
                
                # Сохраняем результат
                cursor.execute("""
                    INSERT INTO similarity_results 
                    (configuration_id, topic_id, topic_type, labor_function_id, rubert_similarity, tfidf_similarity, topic_hours)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    config.config_id,
                    topic_id,
                    'practical',
                    function_id,
                    float(similarity),
                    0.0,  # TF-IDF схожесть пока не рассчитываем
                    0.0   # Часы пока не учитываем
                ))
        
        conn.commit()
        print("\n=== Расчет схожести завершен ===")
        
    finally:
        conn.close()