from typing import List, Dict, Any, Optional, Tuple
import sqlite3
from src.db import get_db_connection
from src.vectorization_config import VectorizationConfig, VectorizationWeight

class VectorizationTextWeights:
    """Класс для подготовки текста с учетом весов при векторизации"""
    
    def __init__(self, config: VectorizationConfig):
        """
        Инициализация обработчика весов текста
        
        Args:
            config: Конфигурация векторизации
        """
        self.config = config
    
    def get_lecture_topic_text(self, topic_id: int, conn: Optional[sqlite3.Connection] = None) -> Tuple[str, float]:
        """
        Получение текста темы лекции с учетом весов
        
        Args:
            topic_id: ID темы лекции
            conn: Соединение с БД
            
        Returns:
            Tuple[str, float]: (текст, вес часов)
        """
        if conn is None:
            conn = get_db_connection()
            should_close = True
        else:
            should_close = False
            
        cursor = conn.cursor()
        
        # Получаем базовую информацию о теме
        cursor.execute("""
            SELECT lt.name, lt.hours, lt.nltk_normalized_name,
                   s.name, s.content, s.nltk_normalized_name, s.nltk_normalized_content,
                   d.goals, d.tasks, d.nltk_normalized_goals, d.nltk_normalized_tasks
            FROM lecture_topics lt
            JOIN sections s ON lt.section_id = s.id
            JOIN disciplines d ON s.discipline_id = d.id
            WHERE lt.id = ?
        """, (topic_id,))
        
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Тема лекции с ID {topic_id} не найдена")
            
        topic_name, hours, topic_norm_name, \
        section_name, section_content, section_norm_name, section_norm_content, \
        discipline_goals, discipline_tasks, discipline_norm_goals, discipline_norm_tasks = row
        
        # Получаем вопросы для самоконтроля
        cursor.execute("""
            SELECT question, nltk_normalized_question
            FROM self_control_questions
            WHERE section_id = (
                SELECT section_id FROM lecture_topics WHERE id = ?
            )
        """, (topic_id,))
        
        questions = cursor.fetchall()
        
        # Формируем текст с учетом весов
        text_parts = []
        hours_weight = 1.0
        
        weights = self.config.get_entity_weights('lecture_topic')
        for weight in weights:
            if weight.source_type == 'name':
                text = topic_norm_name if weight.use_normalized else topic_name
                if text:  # Добавляем только если текст не пустой
                    text_parts.append(text)
                hours_weight = weight.hours_weight
            elif weight.source_type == 'section_name':
                text = section_norm_name if weight.use_normalized else section_name
                if text:  # Добавляем только если текст не пустой
                    text_parts.append(text)
            elif weight.source_type == 'section_content':
                text = section_norm_content if weight.use_normalized else section_content
                if text:  # Добавляем только если текст не пустой
                    text_parts.append(text)
            elif weight.source_type == 'self_control_questions':
                questions_text = ' '.join(
                    q[1] if weight.use_normalized else q[0]
                    for q in questions
                )
                if questions_text:  # Добавляем только если текст не пустой
                    text_parts.append(questions_text)
            elif weight.source_type == 'discipline_goals':
                text = discipline_norm_goals if weight.use_normalized else discipline_goals
                if text:  # Добавляем только если текст не пустой
                    text_parts.append(text)
            elif weight.source_type == 'discipline_tasks':
                text = discipline_norm_tasks if weight.use_normalized else discipline_tasks
                if text:  # Добавляем только если текст не пустой
                    text_parts.append(text)
        
        if should_close:
            conn.close()
            
        return ' '.join(text_parts), hours * hours_weight
    
    def get_practical_topic_text(self, topic_id: int, conn: Optional[sqlite3.Connection] = None) -> Tuple[str, float]:
        """
        Получение текста темы практики с учетом весов
        
        Args:
            topic_id: ID темы практики
            conn: Соединение с БД
            
        Returns:
            Tuple[str, float]: (текст, вес часов)
        """
        if conn is None:
            conn = get_db_connection()
            should_close = True
        else:
            should_close = False
            
        cursor = conn.cursor()
        
        # Получаем базовую информацию о теме
        cursor.execute("""
            SELECT pt.name, pt.hours, pt.nltk_normalized_name,
                   s.name, s.content, s.nltk_normalized_name, s.nltk_normalized_content,
                   d.goals, d.tasks, d.nltk_normalized_goals, d.nltk_normalized_tasks
            FROM practical_topics pt
            JOIN sections s ON pt.section_id = s.id
            JOIN disciplines d ON s.discipline_id = d.id
            WHERE pt.id = ?
        """, (topic_id,))
        
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Тема практики с ID {topic_id} не найдена")
            
        topic_name, hours, topic_norm_name, \
        section_name, section_content, section_norm_name, section_norm_content, \
        discipline_goals, discipline_tasks, discipline_norm_goals, discipline_norm_tasks = row
        
        # Получаем вопросы для самоконтроля
        cursor.execute("""
            SELECT question, nltk_normalized_question
            FROM self_control_questions
            WHERE section_id = (
                SELECT section_id FROM practical_topics WHERE id = ?
            )
        """, (topic_id,))
        
        questions = cursor.fetchall()
        
        # Формируем текст с учетом весов
        text_parts = []
        hours_weight = 1.0
        
        weights = self.config.get_entity_weights('practical_topic')
        for weight in weights:
            if weight.source_type == 'name':
                text = topic_norm_name if weight.use_normalized else topic_name
                if text:  # Добавляем только если текст не пустой
                    text_parts.append(text)
                hours_weight = weight.hours_weight
            elif weight.source_type == 'section_name':
                text = section_norm_name if weight.use_normalized else section_name
                if text:  # Добавляем только если текст не пустой
                    text_parts.append(text)
            elif weight.source_type == 'section_content':
                text = section_norm_content if weight.use_normalized else section_content
                if text:  # Добавляем только если текст не пустой
                    text_parts.append(text)
            elif weight.source_type == 'self_control_questions':
                questions_text = ' '.join(
                    q[1] if weight.use_normalized else q[0]
                    for q in questions
                )
                if questions_text:  # Добавляем только если текст не пустой
                    text_parts.append(questions_text)
            elif weight.source_type == 'discipline_goals':
                text = discipline_norm_goals if weight.use_normalized else discipline_goals
                if text:  # Добавляем только если текст не пустой
                    text_parts.append(text)
            elif weight.source_type == 'discipline_tasks':
                text = discipline_norm_tasks if weight.use_normalized else discipline_tasks
                if text:  # Добавляем только если текст не пустой
                    text_parts.append(text)
        
        if should_close:
            conn.close()
            
        return ' '.join(text_parts), hours * hours_weight
    
    def get_labor_function_text(self, function_id: str, conn: Optional[sqlite3.Connection] = None) -> str:
        """
        Получение текста трудовой функции с учетом весов
        
        Args:
            function_id: ID трудовой функции
            conn: Соединение с БД
            
        Returns:
            str: Текст трудовой функции
        """
        if conn is None:
            conn = get_db_connection()
            should_close = True
        else:
            should_close = False
            
        cursor = conn.cursor()
        
        # Получаем базовую информацию о функции
        cursor.execute("""
            SELECT lf.name, lf.nltk_normalized_name
            FROM labor_functions lf
            WHERE lf.id = ?
        """, (function_id,))
        
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Трудовая функция с ID {function_id} не найдена")
            
        function_name, function_norm_name = row
        
        # Получаем компоненты
        cursor.execute("""
            SELECT lc.description, lc.nltk_normalized_description
            FROM labor_components lc
            WHERE lc.labor_function_id = ?
        """, (function_id,))
        
        components = cursor.fetchall()
        
        # Формируем текст с учетом весов
        text_parts = []
        
        weights = self.config.get_entity_weights('labor_function')
        for weight in weights:
            if weight.source_type == 'name':
                text = function_norm_name if weight.use_normalized else function_name
                if text:  # Добавляем только если текст не пустой
                    text_parts.append(text)
            elif weight.source_type == 'labor_components':
                components_text = ' '.join(
                    c[1] if weight.use_normalized else c[0]
                    for c in components
                )
                if components_text:  # Добавляем только если текст не пустой
                    text_parts.append(components_text)
        
        if should_close:
            conn.close()
            
        return ' '.join(text_parts) 