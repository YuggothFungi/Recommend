from dataclasses import dataclass
from typing import List, Optional
from db import get_db_connection

@dataclass
class VectorizationWeight:
    """Класс для хранения весов векторизации"""
    entity_type: str  # Тип сущности (lecture_topic, practical_topic, labor_function)
    source_type: str  # Тип источника (title, description, name, etc.)
    use_normalized: bool  # Использовать нормализованный текст
    weight: float  # Вес для текста
    hours_weight: Optional[float] = None  # Вес для часов (опционально)

class VectorizationConfig:
    """Класс для работы с конфигурацией векторизации"""
    
    def __init__(self, config_id: int):
        """
        Инициализация конфигурации
        
        Args:
            config_id: ID конфигурации
        """
        self.config_id = config_id
        self.name = None
        self.description = None
        self.config_type = None
        self.weights = {}
        self._load_config()
    
    def _load_config(self):
        """Загрузка конфигурации из базы данных"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Загрузка основной информации о конфигурации
        cursor.execute("""
            SELECT name, description, config_type
            FROM vectorization_configurations
            WHERE id = ?
        """, (self.config_id,))
        
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Конфигурация с ID {self.config_id} не найдена")
            
        self.name = row[0]
        self.description = row[1]
        self.config_type = row[2]
        
        # Загружаем веса
        cursor.execute("""
            SELECT entity_type, source_type, use_normalized, weight, hours_weight
            FROM vectorization_weights
            WHERE configuration_id = ?
            ORDER BY entity_type, source_type
        """, (self.config_id,))
        
        self.weights = {}
        for row in cursor.fetchall():
            weight = VectorizationWeight(
                entity_type=row[0],
                source_type=row[1],
                use_normalized=bool(row[2]),
                weight=float(row[3]),
                hours_weight=float(row[4]) if row[4] is not None else None
            )
            self.weights[f"{weight.entity_type}_{weight.source_type}"] = weight
        
        conn.close()
    
    @classmethod
    def get_available_configs(cls) -> List['VectorizationConfig']:
        """Получение списка доступных конфигураций"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM vectorization_configurations ORDER BY id")
        config_ids = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        
        return [cls(config_id) for config_id in config_ids]
    
    def get_weight(self, entity_type: str, source_type: str) -> Optional[VectorizationWeight]:
        """
        Получение веса для указанного типа сущности и источника
        
        Args:
            entity_type: Тип сущности
            source_type: Тип источника
            
        Returns:
            VectorizationWeight или None, если вес не найден
        """
        return self.weights.get(f"{entity_type}_{source_type}")
        
    def get_entity_weights(self, entity_type: str) -> List[VectorizationWeight]:
        """
        Получение всех весов для указанного типа сущности
        
        Args:
            entity_type: Тип сущности
            
        Returns:
            List[VectorizationWeight]: Список весов для указанного типа сущности
        """
        return [weight for key, weight in self.weights.items() if key.startswith(f"{entity_type}_")] 