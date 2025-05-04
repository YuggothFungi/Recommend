import sys
import os

# Добавляем корневую директорию в PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from src.schema import init_db
from src.data_loader import load_all_data
from src.text_processor import DatabaseTextProcessor
from src.tfidf_vectorizer import DatabaseVectorizer
from src.rubert_vectorizer import RuBertVectorizer
from src.vectorizer import calculate_similarities

def process_data():
    """Главная точка входа для обработки данных"""
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
        print("\n3. Обработка текстов...")
        text_processor = DatabaseTextProcessor()
        text_processor.process_all()
        print("✓ Тексты успешно обработаны")
        
        # 4. Векторизация TF-IDF
        print("\n4. Векторизация TF-IDF...")
        tfidf_vectorizer = DatabaseVectorizer()
        tfidf_vectorizer.vectorize_all()
        print("✓ TF-IDF векторизация успешно завершена")
        
        # 5. Векторизация ruBERT
        print("\n5. Векторизация ruBERT...")
        rubert_vectorizer = RuBertVectorizer()
        rubert_vectorizer.vectorize_all()
        print("✓ ruBERT векторизация успешно завершена")
        
        # 6. Расчет сходства
        print("\n6. Расчет сходства...")
        calculate_similarities()
        print("✓ Расчет сходства успешно завершен")
        
        print("\n" + "=" * 50)
        print(f"Обработка данных завершена: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 50)
        
    except Exception as e:
        print("\n❌ Произошла ошибка:", str(e))
        sys.exit(1)

if __name__ == "__main__":
    process_data() 