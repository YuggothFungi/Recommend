import numpy as np
import sqlite3
import pickle
import logging
from typing import List, Tuple
from src.vector_utils import normalize_vector
from src.db import get_db_connection
from src.vectorization_config import VectorizationConfig
from src.vectorization_text_weights import VectorizationTextWeights

logger = logging.getLogger(__name__)

class VectorStorage:
    """Класс для работы с хранением векторов в базе данных"""
    
    def __init__(self, config_id: int):
        self.config_id = config_id
        self.config = VectorizationConfig(config_id)
        self.text_weights = VectorizationTextWeights(self.config)
    
    def save_vector(self, cursor: sqlite3.Cursor, entity_id: int, 
                   entity_type: str, vector_type: str, vector) -> None:
        """
        Сохранение вектора в базу данных
        
        Args:
            cursor: Курсор базы данных
            entity_id: ID сущности
            entity_type: Тип сущности
            vector_type: Тип вектора
            vector: Вектор для сохранения
        """
        # Нормализуем вектор
        vector = normalize_vector(vector)
        
        # Преобразуем в float32
        vector = vector.astype(np.float32).reshape(-1)
        vector_bytes = vector.tobytes()
        
        # Сохраняем в vectorization_results
        cursor.execute("""
            INSERT INTO vectorization_results 
            (configuration_id, entity_type, entity_id, vector_type, vector_data)
            VALUES (?, ?, ?, ?, ?)
        """, (
            self.config_id,
            entity_type,
            entity_id,
            vector_type,
            vector_bytes
        ))
    
    def get_all_texts(self, cursor: sqlite3.Cursor) -> List[Tuple[str, str, int]]:
        """
        Получение всех текстов из базы данных с учетом конфигурации векторизации
        
        Args:
            cursor: Курсор базы данных
            
        Returns:
            Список кортежей (текст, тип_сущности, id)
        """
        texts = []
        
        # Получаем тексты лекций
        cursor.execute("SELECT id FROM lecture_topics")
        for (lecture_id,) in cursor.fetchall():
            text, _ = self.text_weights.get_lecture_topic_text(lecture_id, cursor.connection)
            texts.append((text, 'lecture_topic', lecture_id))
        
        # Получаем тексты практик
        cursor.execute("SELECT id FROM practical_topics")
        for (practical_id,) in cursor.fetchall():
            text, _ = self.text_weights.get_practical_topic_text(practical_id, cursor.connection)
            texts.append((text, 'practical_topic', practical_id))
        
        # Получаем тексты трудовых функций
        cursor.execute("SELECT id FROM labor_functions")
        for (function_id,) in cursor.fetchall():
            text = self.text_weights.get_labor_function_text(function_id, cursor.connection)
            texts.append((text, 'labor_function', function_id))
        
        return texts 

    def save_keywords(self, cursor, entity_id: int, entity_type: str,
                     config_id: int, keywords: List[Tuple[str, float]]) -> None:
        """
        Сохранение ключевых слов в базу данных
        
        Args:
            cursor: Курсор базы данных
            entity_id: ID сущности
            entity_type: Тип сущности
            config_id: ID конфигурации
            keywords: Список кортежей (слово, вес)
        """
        # Удаляем старые ключевые слова для этой сущности и конфигурации
        cursor.execute("""
            DELETE FROM keywords 
            WHERE entity_type = ? AND entity_id = ? AND configuration_id = ?
        """, (entity_type, entity_id, config_id))
        
        # Сохраняем новые ключевые слова
        cursor.executemany("""
            INSERT INTO keywords 
            (configuration_id, entity_type, entity_id, keyword, weight)
            VALUES (?, ?, ?, ?, ?)
        """, [(config_id, entity_type, entity_id, word, weight) 
              for word, weight in keywords])

    def get_keywords(self, cursor, entity_id: int, entity_type: str,
                    config_id: int, top_n: int = 5) -> List[Tuple[str, float]]:
        """
        Получение ключевых слов для сущности
        
        Args:
            cursor: Курсор базы данных
            entity_id: ID сущности
            entity_type: Тип сущности
            config_id: ID конфигурации
            top_n: Количество ключевых слов
            
        Returns:
            Список кортежей (слово, вес)
        """
        cursor.execute("""
            SELECT keyword, weight
            FROM keywords
            WHERE entity_type = ? AND entity_id = ? AND configuration_id = ?
            ORDER BY weight DESC
            LIMIT ?
        """, (entity_type, entity_id, config_id, top_n))
        
        return cursor.fetchall() 