from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import json
import os
from tfidf_vectorizer import DatabaseVectorizer as TfidfDatabaseVectorizer

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
            vectorizer_type: Тип векторизатора ("tfidf", "word2vec", "sentence_transformer" и т.д.)
        """
        self.vectorizer_type = vectorizer_type
        self.meta_file = 'data/vectorizer_meta.json'
        
        # Выбор конкретной реализации векторизатора
        if vectorizer_type == "tfidf":
            self.vectorizer = TfidfDatabaseVectorizer()
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