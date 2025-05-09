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
            dict: Словарь {entity_id: {'tfidf': vector, 'rubert': vector}}
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
                
                if entity_id not in vectors:
                    vectors[entity_id] = {'tfidf': None, 'rubert': None}
                vectors[entity_id][vector_type] = vector
                
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
        for topic_id, topic_vector_dict in topic_vectors.items():
            for function_id, function_vector_dict in function_vectors.items():
                # Получаем часы для темы
                hours = self._get_topic_hours(cursor, topic_id, topic_type)
                
                # Проверяем существующую запись
                cursor.execute("""
                    SELECT rubert_similarity, tfidf_similarity
                    FROM similarity_results
                    WHERE configuration_id = ? 
                    AND topic_id = ? 
                    AND topic_type = ? 
                    AND labor_function_id = ?
                """, (self.config.config_id, topic_id, topic_type, function_id))
                
                existing = cursor.fetchone()
                rubert_similarity = existing[0] if existing else 0.0
                tfidf_similarity = existing[1] if existing else 0.0
                
                # Рассчитываем сходство для каждого типа вектора
                if topic_vector_dict['rubert'] is not None and function_vector_dict['rubert'] is not None:
                    rubert_similarity = np.dot(topic_vector_dict['rubert'], function_vector_dict['rubert'])
                    if np.isnan(rubert_similarity):
                        rubert_similarity = 0.0
                
                if topic_vector_dict['tfidf'] is not None and function_vector_dict['tfidf'] is not None:
                    tfidf_similarity = np.dot(topic_vector_dict['tfidf'], function_vector_dict['tfidf'])
                    if np.isnan(tfidf_similarity):
                        tfidf_similarity = 0.0
                
                # Сохраняем результат
                cursor.execute("""
                    INSERT INTO similarity_results 
                    (configuration_id, topic_id, topic_type, labor_function_id, 
                     rubert_similarity, tfidf_similarity, topic_hours)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(configuration_id, topic_id, topic_type, labor_function_id) 
                    DO UPDATE SET
                        rubert_similarity = excluded.rubert_similarity,
                        tfidf_similarity = excluded.tfidf_similarity,
                        topic_hours = excluded.topic_hours
                """, (
                    self.config.config_id,
                    topic_id,
                    topic_type,
                    function_id,
                    float(rubert_similarity),
                    float(tfidf_similarity),
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