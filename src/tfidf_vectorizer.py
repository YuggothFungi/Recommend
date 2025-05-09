from typing import List, Dict, Any
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer as SklearnTfidfVectorizer
import pickle
import os
from vectorization_config import VectorizationConfig

class TfidfDatabaseVectorizer:
    """
    Класс для векторизации текстов с использованием TF-IDF.
    
    Предполагает, что тексты уже нормализованы и сохранены в базе данных
    в колонках с префиксом 'nltk_normalized_'.
    
    Нормализация текста должна включать:
    - Лемматизацию
    - Удаление стоп-слов
    - Обработку тематических словосочетаний
    - Приведение к нижнему регистру
    - Удаление специальных символов
    
    Этот класс отвечает только за преобразование нормализованных текстов в TF-IDF векторы.
    """
    
    def __init__(self, config: VectorizationConfig):
        """
        Инициализация TF-IDF векторизатора
        
        Args:
            config: Конфигурация векторизации
        """
        self.config = config
        self.vectorizer = SklearnTfidfVectorizer(
            max_features=5000,  # Уменьшаем размерность для ускорения
            min_df=3,          # Игнорируем редкие термины
            max_df=0.85,       # Игнорируем слишком частые термины
            ngram_range=(1, 2) # Учитываем биграммы для лучшего улавливания контекста
        )
    
    def fit_transform(self, texts: List[str]) -> np.ndarray:
        """
        Обучение и преобразование нормализованных текстов в векторы
        
        Args:
            texts: Список нормализованных текстов
            
        Returns:
            Массив TF-IDF векторов
        """
        return self.vectorizer.fit_transform(texts)
    
    def transform(self, texts: List[str]) -> np.ndarray:
        """
        Преобразование нормализованных текстов в векторы
        
        Args:
            texts: Список нормализованных текстов
            
        Returns:
            Массив TF-IDF векторов (нормализованных)
        """
        vectors = self.vectorizer.transform(texts)
        # Нормализуем векторы
        vectors = vectors.toarray()  # Преобразуем в плотный массив
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        vectors = vectors / norms
        return vectors
    
    def save_meta(self, meta_file: str) -> None:
        """
        Сохранение обученного векторизатора
        
        Args:
            meta_file: Путь к файлу для сохранения
        """
        os.makedirs(os.path.dirname(meta_file), exist_ok=True)
        with open(meta_file, 'wb') as f:
            pickle.dump(self.vectorizer, f)
    
    def load_meta(self, meta_file: str) -> None:
        """
        Загрузка обученного векторизатора
        
        Args:
            meta_file: Путь к файлу с сохраненным векторизатором
        """
        with open(meta_file, 'rb') as f:
            self.vectorizer = pickle.load(f) 