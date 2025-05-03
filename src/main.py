import os
import sys
from datetime import datetime
from schema import init_db
from data_loader import load_all_data
from text_processor import DatabaseTextProcessor
from vectorizer import DatabaseVectorizer

def main():
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
        
        # 4. Векторизация
        print("\n4. Векторизация...")
        # Используем TF-IDF векторизатор по умолчанию
        vectorizer = DatabaseVectorizer(vectorizer_type="tfidf")
        vectorizer.vectorize_all()
        print("✓ Векторизация успешно завершена")
        
        print("\n" + "=" * 50)
        print(f"Обработка данных завершена: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 50)
        
    except Exception as e:
        print("\n❌ Произошла ошибка:", str(e))
        sys.exit(1)

if __name__ == "__main__":
    main() 