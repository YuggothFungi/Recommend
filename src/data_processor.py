import sys
import os
import logging

# Добавляем корневую директорию в PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from src.schema import init_db
from src.data_loader import load_all_data
from src.text_processor import DatabaseTextProcessor
from src.vectorizer import Vectorizer
from src.similarity_calculator import SimilarityCalculator
from src.vectorization_config import VectorizationConfig

logger = logging.getLogger(__name__)

def process_data():
    """Полный цикл обработки данных"""
    print("=" * 50)
    print(f"Начало обработки данных: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    try:
        # 1. Инициализация базы данных
        print("\n1. Инициализация базы данных...")
        init_db()
        print("✓ База данных успешно инициализирована")
        
        # 2. Загрузка данных
        print("\n2. Загрузка данных...")
        load_all_data()
        print("✓ Данные успешно загружены")
        
        # 3. Обработка текстов
        logger.info("Обработка текстов...")
        processor = DatabaseTextProcessor()
        processor.process_all()
        print("✓ Тексты успешно обработаны")
        
        # 4. Векторизация
        logger.info("Векторизация...")
        config = VectorizationConfig(1)  # Используем первую конфигурацию по умолчанию
        vectorizer = Vectorizer(config)
        vectorizer.vectorize_all()
        print("✓ Векторизация успешно завершена")
        
        # 5. Расчет сходств
        logger.info("Расчет сходств...")
        similarity_calculator = SimilarityCalculator(config)
        similarity_calculator.calculate_similarities()
        print("✓ Расчет сходства успешно завершен")
        
        print("\n" + "=" * 50)
        print(f"Обработка данных завершена: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 50)
        
    except Exception as e:
        print("\n❌ Произошла ошибка:", str(e))
        sys.exit(1)

if __name__ == "__main__":
    process_data() 