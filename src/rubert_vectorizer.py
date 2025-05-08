import torch
from transformers import AutoTokenizer, AutoModel
from typing import List, Dict, Any
import numpy as np
import json
import os
import sqlite3
from src.db import get_db_connection
from src.check_normalized_texts import check_normalized_texts
from src.vectorization_config import VectorizationConfig
from src.vectorization_text_weights import VectorizationTextWeights

class RuBertVectorizer:
    """Векторизатор на основе ruBERT"""
    
    def __init__(self, config: VectorizationConfig, conn=None):
        """
        Инициализация векторизатора
        
        Args:
            config: Конфигурация векторизации
            conn: Соединение с базой данных (опционально)
        """
        self.model_name = 'sberbank-ai/sbert_large_nlu_ru'
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModel.from_pretrained(self.model_name)
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model.to(self.device)
        self.model.eval()
        self.vector_size = 1024  # Размер вектора для sbert_large_nlu_ru
        self.db_conn = conn  # Использовать переданное соединение
        self.config = config
        self.text_weights = VectorizationTextWeights(config)
    
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
        cursor.execute("SELECT id FROM lecture_topics")
        lecture_topics = cursor.fetchall()
        
        cursor.execute("SELECT id FROM practical_topics")
        practical_topics = cursor.fetchall()
        
        result = []
        for topic_id, in lecture_topics:
            text, _ = self.text_weights.get_lecture_topic_text(topic_id, cursor.connection)
            result.append((topic_id, text))
        
        for topic_id, in practical_topics:
            text, _ = self.text_weights.get_practical_topic_text(topic_id, cursor.connection)
            result.append((topic_id, text))
        
        return result
    
    def _get_labor_function_texts(self, cursor):
        """Получение объединенных нормализованных текстов трудовых функций"""
        cursor.execute("SELECT id FROM labor_functions")
        labor_functions = cursor.fetchall()
        
        result = []
        for function_id, in labor_functions:
            text = self.text_weights.get_labor_function_text(function_id, cursor.connection)
            result.append((function_id, text))
        
        return result
    
    def _save_vector(self, cursor, entity_type: str, entity_id: int, vector: np.ndarray) -> None:
        """Сохранение вектора в базу данных"""
        vector_bytes = vector.tobytes()
        
        # Сохраняем в vectorization_results
        cursor.execute("""
            INSERT INTO vectorization_results 
            (configuration_id, entity_type, entity_id, vector_type, vector_data)
            VALUES (?, ?, ?, ?, ?)
        """, (
            self.config.config_id,
            entity_type,
            entity_id,
            'rubert',
            vector_bytes
        ))
    
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
            self._save_vector(cursor, 'lecture_topic' if topic_id in [t[0] for t in topic_texts[:len(topic_texts)//2]] else 'practical_topic', topic_id, vector)
        
        # Векторизуем трудовые функции
        print("Векторизация трудовых функций...")
        function_texts_only = [text for _, text in function_texts]
        function_vectors = self.transform(function_texts_only)
        
        for (function_id, _), vector in zip(function_texts, function_vectors):
            self._save_vector(cursor, 'labor_function', function_id, vector)
        
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