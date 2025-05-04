from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import json
import os
from src.tfidf_vectorizer import DatabaseVectorizer as TfidfDatabaseVectorizer
from src.rubert_vectorizer import RuBertVectorizer
import pickle
import numpy as np
from src.db import get_db_connection

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
            vectorizer_type: Тип векторизатора ("tfidf", "rubert")
        """
        self.vectorizer_type = vectorizer_type
        self.meta_file = 'data/vectorizer_meta.json'
        
        # Выбор конкретной реализации векторизатора
        if vectorizer_type == "tfidf":
            self.vectorizer = TfidfDatabaseVectorizer()
        elif vectorizer_type == "rubert":
            self.vectorizer = RuBertVectorizer()
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

def calculate_similarities(conn=None):
    """Расчет сходства между темами и трудовыми функциями"""
    if conn is None:
        conn = get_db_connection()
        should_close = True
    else:
        should_close = False
        
    cursor = conn.cursor()
    
    # Проверяем существование таблиц
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name IN ('topic_vectors', 'labor_function_vectors', 'topic_labor_function')
    """)
    existing_tables = {row[0] for row in cursor.fetchall()}
    
    if 'topic_vectors' not in existing_tables or 'labor_function_vectors' not in existing_tables:
        print("Ошибка: таблицы с векторами не существуют")
        if should_close:
            conn.close()
        return
    
    # Создаем таблицу для результатов, если её нет
    if 'topic_labor_function' not in existing_tables:
        cursor.execute("""
            CREATE TABLE topic_labor_function (
                topic_id INTEGER,
                labor_function_id TEXT,
                tfidf_similarity REAL,
                rubert_similarity REAL,
                PRIMARY KEY (topic_id, labor_function_id),
                FOREIGN KEY (topic_id) REFERENCES topics(id),
                FOREIGN KEY (labor_function_id) REFERENCES labor_functions(id)
            )
        """)
        conn.commit()
    
    # Очищаем существующие значения
    cursor.execute("DELETE FROM topic_labor_function")
    conn.commit()
    
    # Получаем все вектора тем
    cursor.execute("""
        SELECT topic_id, tfidf_vector, rubert_vector
        FROM topic_vectors
        WHERE tfidf_vector IS NOT NULL OR rubert_vector IS NOT NULL
    """)
    topic_vectors = cursor.fetchall()
    
    if not topic_vectors:
        print("Ошибка: нет векторов тем")
        if should_close:
            conn.close()
        return
    
    # Получаем все вектора трудовых функций
    cursor.execute("""
        SELECT labor_function_id, tfidf_vector, rubert_vector
        FROM labor_function_vectors
        WHERE tfidf_vector IS NOT NULL OR rubert_vector IS NOT NULL
    """)
    function_vectors = cursor.fetchall()
    
    if not function_vectors:
        print("Ошибка: нет векторов трудовых функций")
        if should_close:
            conn.close()
        return
    
    # Для каждой пары считаем сходство
    total_pairs = len(topic_vectors) * len(function_vectors)
    processed_pairs = 0
    
    for topic_id, topic_tfidf, topic_rubert in topic_vectors:
        for function_id, function_tfidf, function_rubert in function_vectors:
            processed_pairs += 1
            if processed_pairs % 100 == 0:
                print(f"Обработано {processed_pairs}/{total_pairs} пар")
            
            tfidf_sim = 0.0
            rubert_sim = 0.0
            
            # Сходство по TF-IDF
            if topic_tfidf and function_tfidf:
                try:
                    # Читаем векторы как float32
                    topic_tfidf_vec = np.frombuffer(topic_tfidf, dtype=np.float32)
                    function_tfidf_vec = np.frombuffer(function_tfidf, dtype=np.float32)
                    
                    # Проверяем, что размеры векторов совпадают
                    if topic_tfidf_vec.shape != function_tfidf_vec.shape:
                        print(f"Пропуск: разные размеры векторов для темы {topic_id} и функции {function_id}")
                        continue
                    
                    # Проверяем, что векторы не нулевые
                    if np.all(topic_tfidf_vec == 0) or np.all(function_tfidf_vec == 0):
                        print(f"Пропуск: нулевой вектор для темы {topic_id} и функции {function_id}")
                        continue
                    
                    # Нормализуем векторы
                    topic_norm = np.linalg.norm(topic_tfidf_vec)
                    function_norm = np.linalg.norm(function_tfidf_vec)
                    
                    if topic_norm == 0 or function_norm == 0:
                        print(f"Пропуск: нулевая норма вектора для темы {topic_id} и функции {function_id}")
                        continue
                        
                    topic_tfidf_vec = topic_tfidf_vec / topic_norm
                    function_tfidf_vec = function_tfidf_vec / function_norm
                    
                    # Считаем косинусное сходство
                    tfidf_sim = float(np.dot(topic_tfidf_vec, function_tfidf_vec))
                    
                    # Проверяем корректность значения
                    if not (0 <= tfidf_sim <= 1):
                        print(f"Предупреждение: некорректное значение TF-IDF сходства {tfidf_sim} для темы {topic_id} и функции {function_id}")
                        tfidf_sim = max(0.0, min(1.0, tfidf_sim))
                    
                except Exception as e:
                    print(f"Ошибка при расчете TF-IDF сходства для темы {topic_id} и функции {function_id}: {e}")
                    continue
            
            # Сходство по ruBERT
            if topic_rubert and function_rubert:
                try:
                    topic_rubert_vec = np.frombuffer(topic_rubert, dtype=np.float32)
                    function_rubert_vec = np.frombuffer(function_rubert, dtype=np.float32)
                    
                    # Нормализуем векторы
                    topic_norm = np.linalg.norm(topic_rubert_vec)
                    function_norm = np.linalg.norm(function_rubert_vec)
                    
                    if topic_norm == 0 or function_norm == 0:
                        print(f"Пропуск: нулевая норма ruBERT вектора для темы {topic_id} и функции {function_id}")
                        continue
                        
                    topic_rubert_vec = topic_rubert_vec / topic_norm
                    function_rubert_vec = function_rubert_vec / function_norm
                    
                    rubert_sim = float(np.dot(topic_rubert_vec, function_rubert_vec))
                    
                    # Проверяем корректность значения
                    if not (0 <= rubert_sim <= 1):
                        print(f"Предупреждение: некорректное значение ruBERT сходства {rubert_sim} для темы {topic_id} и функции {function_id}")
                        rubert_sim = max(0.0, min(1.0, rubert_sim))
                        
                except Exception as e:
                    print(f"Ошибка при расчете ruBERT сходства для темы {topic_id} и функции {function_id}: {e}")
                    continue
            
            try:
                # Сохраняем сходство
                cursor.execute("""
                    INSERT OR REPLACE INTO topic_labor_function 
                    (topic_id, labor_function_id, tfidf_similarity, rubert_similarity)
                    VALUES (?, ?, ?, ?)
                """, (topic_id, function_id, tfidf_sim, rubert_sim))
                
                # Коммитим каждые 100 записей для оптимизации производительности
                if processed_pairs % 100 == 0:
                    conn.commit()
                    
            except Exception as e:
                print(f"Ошибка при сохранении сходства для темы {topic_id} и функции {function_id}: {e}")
                continue
    
    # Финальный коммит
    conn.commit()
    
    # Проверяем результаты
    cursor.execute("SELECT COUNT(*) FROM topic_labor_function WHERE tfidf_similarity > 0")
    tfidf_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM topic_labor_function WHERE rubert_similarity > 0")
    rubert_count = cursor.fetchone()[0]
    
    print(f"\nСтатистика:")
    print(f"Всего пар: {total_pairs}")
    print(f"Пар с ненулевым TF-IDF сходством: {tfidf_count}")
    print(f"Пар с ненулевым ruBERT сходством: {rubert_count}")
    
    if should_close:
        conn.close()