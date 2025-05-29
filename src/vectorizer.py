from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import json
import os
from tfidf_vectorizer import TfidfDatabaseVectorizer
from rubert_vectorizer import RuBertVectorizer
import pickle
import numpy as np
from db import get_db_connection
from vectorization_config import VectorizationConfig
from vectorization_text_weights import VectorizationTextWeights
from vector_storage import VectorStorage
import sqlite3
import logging

logger = logging.getLogger(__name__)

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
    """Класс для векторизации текстов с использованием различных методов"""
    
    def __init__(self, config_id: int, vectorizer_type: str):
        """
        Инициализация векторизатора
        
        Args:
            config_id: ID конфигурации векторизации
            vectorizer_type: Тип векторизатора ('tfidf' или 'rubert')
        """
        self.config = VectorizationConfig(config_id)
        self.vectorizer_type = vectorizer_type
        
        if vectorizer_type == 'tfidf':
            self.vectorizer = TfidfDatabaseVectorizer(self.config)
        elif vectorizer_type == 'rubert':
            self.vectorizer = RuBertVectorizer(self.config)
        else:
            raise ValueError(f"Неизвестный тип векторизатора: {vectorizer_type}")
            
        self.storage = VectorStorage(config_id)
    
    def vectorize_all(self, conn=None):
        """Векторизация всех текстов"""
        logger.info(f"\n=== Начало векторизации (тип: {self.vectorizer_type}) ===")
        
        if conn is None:
            conn = get_db_connection()
            should_close = True
        else:
            should_close = False
            
        cursor = conn.cursor()
        
        # Получаем все тексты
        texts_data = self.storage.get_all_texts(cursor)
        all_texts = [text for text, _, _ in texts_data]
        
        # Векторизуем все тексты сразу
        logger.info("\nВекторизация текстов...")
        vectors = self.vectorizer.fit_transform(all_texts)
        
        # Сохраняем векторы и ключевые слова
        for (text, entity_type, entity_id), vector in zip(texts_data, vectors):
            # Сохраняем вектор
            self.storage.save_vector(cursor, entity_id, entity_type, 
                                   self.vectorizer_type, vector)
            
            # Извлекаем и сохраняем ключевые слова
            if self.vectorizer_type == 'tfidf':
                keywords = self.vectorizer.extract_keywords(text)
                self.storage.save_keywords(cursor, entity_id, entity_type,
                                        self.config.config_id, keywords)
        
        conn.commit()
        
        if should_close:
            conn.close()
            
        logger.info("Векторизация завершена!")