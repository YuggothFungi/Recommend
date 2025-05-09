import numpy as np
from src.db import get_db_connection
from src.vectorization_config import VectorizationConfig
import logging

logger = logging.getLogger(__name__)

class SimilarityCalculator:
    """Класс для вычисления сходства между векторами"""
    
    def __init__(self, config: VectorizationConfig):
        """
        Инициализация калькулятора сходства
        
        Args:
            config: Конфигурация векторизации
        """
        self.config = config
    
    def calculate_similarities(self, conn=None):
        """Расчет схожести между векторами"""
        logger.info("\n=== Начало расчета схожести ===")
        
        if conn is None:
            conn = get_db_connection()
            should_close = True
        else:
            should_close = False
            
        cursor = conn.cursor()
        
        try:
            # Загрузка векторов
            lecture_vectors = self._load_vectors(cursor, 'lecture_topic')
            practical_vectors = self._load_vectors(cursor, 'practical_topic')
            labor_vectors = self._load_vectors(cursor, 'labor_function')
            
            # Расчет схожести
            logger.info("\nРасчет схожести...")
            
            # Для лекций
            self._calculate_and_save_similarities(
                cursor, lecture_vectors, labor_vectors, 'lecture'
            )
            
            # Для практик
            self._calculate_and_save_similarities(
                cursor, practical_vectors, labor_vectors, 'practical'
            )
            
            conn.commit()
            logger.info("\n=== Расчет схожести завершен ===")
            
        finally:
            if should_close:
                conn.close()
    
    def _load_vectors(self, cursor, entity_type: str) -> dict:
        """
        Загрузка векторов из базы данных
        
        Args:
            cursor: Курсор базы данных
            entity_type: Тип сущности
            
        Returns:
            dict: Словарь {entity_id: vector}
        """
        vectors = {}
        
        cursor.execute("""
            SELECT entity_id, vector_data, vector_type
            FROM vectorization_results 
            WHERE configuration_id = ? AND entity_type = ?
        """, (self.config.config_id, entity_type))
        
        for entity_id, vector_bytes, vector_type in cursor.fetchall():
            try:
                vector = np.frombuffer(vector_bytes, dtype=np.float32)
                norm = np.linalg.norm(vector)
                logger.debug(f"{entity_type} {entity_id} ({vector_type}): норма = {norm}")
                
                if not np.isclose(norm, 1.0, rtol=1e-5):
                    logger.warning(f"Vector {entity_id} ({vector_type}) is not normalized. Norm: {norm}")
                    vector = vector / norm
                    
                vectors[entity_id] = vector
            except Exception as e:
                logger.error(f"Error loading vector {entity_id}: {str(e)}")
        
        return vectors
    
    def _calculate_and_save_similarities(self, cursor, topic_vectors: dict, 
                                      function_vectors: dict, topic_type: str):
        """
        Расчет и сохранение сходства между темами и трудовыми функциями
        
        Args:
            cursor: Курсор базы данных
            topic_vectors: Словарь векторов тем
            function_vectors: Словарь векторов трудовых функций
            topic_type: Тип темы ('lecture' или 'practical')
        """
        for topic_id, topic_vector in topic_vectors.items():
            for function_id, function_vector in function_vectors.items():
                similarity = np.dot(topic_vector, function_vector)
                logger.debug(f"{topic_type} {topic_id} - Трудовая функция {function_id}: {similarity}")
                
                # Проверяем на nan и заменяем на 0.0
                if np.isnan(similarity):
                    similarity = 0.0
                
                # Получаем часы для темы
                hours = self._get_topic_hours(cursor, topic_id, topic_type)
                
                # Сохраняем результат
                cursor.execute("""
                    INSERT INTO similarity_results 
                    (configuration_id, topic_id, topic_type, labor_function_id, 
                     rubert_similarity, tfidf_similarity, topic_hours)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.config.config_id,
                    topic_id,
                    topic_type,
                    function_id,
                    float(similarity),
                    0.0,  # TF-IDF схожесть пока не рассчитываем
                    hours
                ))
    
    def _get_topic_hours(self, cursor, topic_id: int, topic_type: str) -> float:
        """
        Получение количества часов для темы
        
        Args:
            cursor: Курсор базы данных
            topic_id: ID темы
            topic_type: Тип темы ('lecture' или 'practical')
            
        Returns:
            float: Количество часов
        """
        table = 'lecture_topics' if topic_type == 'lecture' else 'practical_topics'
        cursor.execute(f"SELECT hours FROM {table} WHERE id = ?", (topic_id,))
        result = cursor.fetchone()
        return float(result[0]) if result else 0.0 