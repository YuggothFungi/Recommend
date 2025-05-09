import numpy as np
import sqlite3
import pickle
import logging
from typing import List, Tuple
from vector_utils import normalize_vector
from db import get_db_connection

logger = logging.getLogger(__name__)

class VectorStorage:
    """Класс для работы с хранением векторов в базе данных"""
    
    def __init__(self, config_id: int):
        self.config_id = config_id
    
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
        Получение всех текстов из базы данных
        
        Args:
            cursor: Курсор базы данных
            
        Returns:
            Список кортежей (текст, тип_сущности, id)
        """
        texts = []
        
        # Получаем тексты лекций
        cursor.execute("""
            SELECT id, name, nltk_normalized_name 
            FROM lecture_topics
        """)
        for lecture_id, name, normalized_name in cursor.fetchall():
            text = normalized_name if normalized_name else name
            texts.append((text, 'lecture_topic', lecture_id))
        
        # Получаем тексты практик
        cursor.execute("""
            SELECT id, name, nltk_normalized_name 
            FROM practical_topics
        """)
        for practical_id, name, normalized_name in cursor.fetchall():
            text = normalized_name if normalized_name else name
            texts.append((text, 'practical_topic', practical_id))
        
        # Получаем тексты трудовых функций
        cursor.execute("""
            SELECT id, name, nltk_normalized_name 
            FROM labor_functions
        """)
        for function_id, name, normalized_name in cursor.fetchall():
            text = normalized_name if normalized_name else name
            texts.append((text, 'labor_function', function_id))
        
        return texts 