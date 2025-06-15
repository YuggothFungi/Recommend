import time
import psutil
import numpy as np
from typing import List, Dict, Any
import logging
from src.vectorizer import Vectorizer
from src.similarity_calculator import SimilarityCalculator
from src.vectorization_config import VectorizationConfig
from src.db import get_db_connection
from src.vectorization_text_weights import VectorizationTextWeights

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorizationBenchmark:
    """Класс для бенчмаркинга методов векторизации"""
    
    def __init__(self, config_id: int):
        """
        Инициализация бенчмарка
        
        Args:
            config_id: ID конфигурации векторизации
        """
        self.config = VectorizationConfig(config_id)
        self.process = psutil.Process()

    def measure_peak_memory(self, func, *args, **kwargs) -> float:
        """
        Измерение пикового использования памяти во время выполнения функции
        """
        peak_memory = 0.0
        start_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        func(*args, **kwargs)
        current_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        peak_memory = max(peak_memory, current_memory - start_memory)
        return peak_memory

    def measure_cpu_usage(self, func, *args, **kwargs) -> float:
        """
        Измерение среднего использования CPU во время выполнения функции
        """
        cpu_percent = self.process.cpu_percent(interval=1.0)
        func(*args, **kwargs)
        return cpu_percent

    def benchmark_vectorizer(self, vectorizer_type: str) -> Dict[str, float]:
        """
        Бенчмарк для одного векторизатора
        Возвращает общее время, среднее время на вектор, количество векторов и статистику по сходствам.
        """
        logger.info(f"\n=== Бенчмарк векторизатора {vectorizer_type} ===")
        
        # Векторизация
        vectorizer = Vectorizer(config_id=self.config.config_id, vectorizer_type=vectorizer_type)
        start_time = time.time()
        peak_memory = self.measure_peak_memory(vectorizer.vectorize_all)
        cpu_usage = self.measure_cpu_usage(vectorizer.vectorize_all)
        end_time = time.time()
        vectorization_time = end_time - start_time

        # Получаем количество векторов и среднее количество слов
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as total_vectors
            FROM vectorization_results
            WHERE configuration_id = ? AND vector_type = ?
        """, (self.config.config_id, vectorizer_type))
        total_vectors = cursor.fetchone()[0]

        # Получаем все тексты для подсчёта среднего количества слов
        text_weights = VectorizationTextWeights(self.config)
        total_words = 0
        total_texts = 0

        # Лекционные темы
        cursor.execute("SELECT id FROM lecture_topics")
        for (topic_id,) in cursor.fetchall():
            text, _ = text_weights.get_lecture_topic_text(topic_id, conn)
            total_words += len(text.split())
            total_texts += 1

        # Практические темы
        cursor.execute("SELECT id FROM practical_topics")
        for (topic_id,) in cursor.fetchall():
            text, _ = text_weights.get_practical_topic_text(topic_id, conn)
            total_words += len(text.split())
            total_texts += 1

        # Трудовые функции
        cursor.execute("SELECT id FROM labor_functions")
        for (function_id,) in cursor.fetchall():
            text = text_weights.get_labor_function_text(function_id, conn)
            total_words += len(text.split())
            total_texts += 1

        avg_words_per_text = total_words / total_texts if total_texts > 0 else 0

        avg_time_per_vector = vectorization_time / total_vectors if total_vectors else 0.0

        # Расчет сходств
        calculator = SimilarityCalculator(self.config)
        start_sim_time = time.time()
        calculator.calculate_similarities()
        end_sim_time = time.time()
        similarity_time = end_sim_time - start_sim_time

        # Статистика по сходствам
        cursor.execute("""
            SELECT COUNT(*) as total_similarities,
                   AVG(CASE 
                       WHEN ? = 'tfidf' THEN tfidf_similarity 
                       ELSE rubert_similarity 
                   END) as avg_similarity,
                   MIN(CASE 
                       WHEN ? = 'tfidf' THEN tfidf_similarity 
                       ELSE rubert_similarity 
                   END) as min_similarity,
                   MAX(CASE 
                       WHEN ? = 'tfidf' THEN tfidf_similarity 
                       ELSE rubert_similarity 
                   END) as max_similarity
            FROM similarity_results
            WHERE configuration_id = ?
        """, (vectorizer_type, vectorizer_type, vectorizer_type, self.config.config_id))
        total_similarities, avg_similarity, min_similarity, max_similarity = cursor.fetchone()
        conn.close()

        return {
            'vectorization_time': vectorization_time,
            'avg_time_per_vector': avg_time_per_vector,
            'total_vectors': total_vectors,
            'similarity_time': similarity_time,
            'total_similarities': total_similarities,
            'avg_similarity': avg_similarity,
            'min_similarity': min_similarity,
            'max_similarity': max_similarity,
            'peak_memory': peak_memory,
            'cpu_usage': cpu_usage,
            'avg_words_per_text': avg_words_per_text
        }

    def run_benchmark(self) -> Dict[str, Dict[str, float]]:
        """
        Запуск бенчмарка для всех векторизаторов
        
        Returns:
            Словарь с результатами бенчмарка для каждого векторизатора
        """
        results = {}
        results['tfidf'] = self.benchmark_vectorizer('tfidf')
        results['rubert'] = self.benchmark_vectorizer('rubert')
        return results

    def print_results(self, results: Dict[str, Dict[str, float]]):
        """
        Вывод результатов бенчмарка
        
        Args:
            results: Результаты бенчмарка
        """
        print("\n=== Результаты бенчмарка ===")
        print(f"Конфигурация: {self.config.config_id}")
        print(f"Тип конфигурации: {self.config.config_type}")
        print(f"Описание: {self.config.description}")
        
        for vectorizer_type, metrics in results.items():
            print(f"\n{vectorizer_type.upper()}:")
            print(f"Время векторизации: {metrics['vectorization_time']:.2f} сек")
            print(f"Среднее время на один вектор: {metrics['avg_time_per_vector']:.4f} сек")
            print(f"Всего векторов: {metrics['total_vectors']}")
            print(f"Среднее количество слов на текст: {metrics['avg_words_per_text']:.1f}")
            print(f"Время расчета сходств: {metrics['similarity_time']:.2f} сек")
            print(f"Всего сходств: {metrics['total_similarities']}")
            print(f"Среднее сходство: {metrics['avg_similarity']:.4f}")
            print(f"Минимальное сходство: {metrics['min_similarity']:.4f}")
            print(f"Максимальное сходство: {metrics['max_similarity']:.4f}")
            print(f"Пиковое использование памяти: {metrics['peak_memory']:.2f} MB")
            print(f"Среднее использование CPU: {metrics['cpu_usage']:.2f}%") 