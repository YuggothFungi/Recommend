from typing import List, Dict, Any, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer as SklearnTfidfVectorizer
import pickle
import os
from scipy import sparse
from src.vectorization_config import VectorizationConfig
from src.vectorization_text_weights import VectorizationTextWeights
from src.db import get_db_connection

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
    
    # Общий векторизатор для всех экземпляров
    _shared_vectorizer = SklearnTfidfVectorizer(
        max_features=5000,  # Уменьшаем размерность для ускорения
        min_df=1,          # Учитываем все термины
        max_df=1.0,        # Учитываем все термины
        ngram_range=(1, 2) # Учитываем биграммы для лучшего улавливания контекста
    )
    
    def __init__(self, config: VectorizationConfig):
        """
        Инициализация TF-IDF векторизатора
        
        Args:
            config: Конфигурация векторизации
        """
        self.config = config
        self.vectorizer = self._shared_vectorizer
        self.is_fitted = False
    
    def _apply_weights(self, vectors: np.ndarray, weights: List[List[Any]]) -> np.ndarray:
        """
        Применение весов к векторам
        
        Args:
            vectors: Массив векторов
            weights: Список списков весов (каждый внутренний список содержит объекты VectorizationWeight)
            
        Returns:
            Массив взвешенных векторов
        """
        # Преобразуем веса в массив numpy, учитывая только числовые веса
        weight_array = np.array([sum(w.weight for w in weight_list) for weight_list in weights]).reshape(-1, 1)
        
        # Применяем веса к векторам
        weighted_vectors = vectors * weight_array
        
        # Нормализуем векторы
        norms = np.linalg.norm(weighted_vectors, axis=1, keepdims=True)
        weighted_vectors = weighted_vectors / norms
        
        return weighted_vectors
    
    def fit(self, texts: List[str]) -> None:
        """
        Обучение векторизатора на всех текстах
        
        Args:
            texts: Список всех текстов для обучения
        """
        self.vectorizer.fit(texts)
        self.is_fitted = True
    
    def transform(self, texts: List[str]) -> np.ndarray:
        """
        Преобразование нормализованных текстов в векторы
        
        Args:
            texts: Список нормализованных текстов
            
        Returns:
            Массив TF-IDF векторов (нормализованных)
        """
        if not self.is_fitted:
            raise ValueError("Векторизатор не обучен. Сначала вызовите метод fit()")
        
        # Получаем базовые векторы
        vectors = self.vectorizer.transform(texts).toarray()
        
        # Получаем веса для каждого типа сущности
        weights = []
        for text in texts:
            if 'lecture_topic' in text:
                weights.append(self.config.get_entity_weights('lecture_topic'))
            elif 'practical_topic' in text:
                weights.append(self.config.get_entity_weights('practical_topic'))
            else:
                weights.append(self.config.get_entity_weights('labor_function'))
        
        # Применяем веса к векторам
        return self._apply_weights(vectors, weights)
    
    def fit_transform(self, texts: List[str]) -> np.ndarray:
        """
        Обучение и преобразование нормализованных текстов в векторы
        
        Args:
            texts: Список нормализованных текстов
            
        Returns:
            Массив TF-IDF векторов
        """
        self.fit(texts)
        return self.transform(texts)
    
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

    def extract_keywords(self, text: str, top_n: int = 5) -> List[Tuple[str, float]]:
        """
        Извлечение ключевых слов из текста
        
        Args:
            text: Текст для анализа
            top_n: Количество ключевых слов
            
        Returns:
            Список кортежей (слово, вес)
        """
        if not self.is_fitted:
            raise ValueError("Векторизатор не обучен. Сначала вызовите метод fit()")
            
        # Получаем вектор для текста
        vector = self.vectorizer.transform([text])
        
        # Получаем все термины
        feature_names = self.vectorizer.get_feature_names_out()
        
        # Получаем веса для каждого термина
        weights = vector.toarray()[0]
        
        # Сортируем термины по весу
        sorted_indices = weights.argsort()[::-1]
        
        # Возвращаем top_n ключевых слов с их весами
        return [(feature_names[i], weights[i]) for i in sorted_indices[:top_n]] 