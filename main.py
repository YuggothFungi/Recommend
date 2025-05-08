#!/usr/bin/env python3
"""
Главный файл запуска приложения.
Проверяет зависимости и запускает основную логику из src/data_processor.py
"""

import sys
import pkg_resources
import subprocess
from pathlib import Path
import argparse
from src.text_processor import DatabaseTextProcessor
from src.vectorizer import DatabaseVectorizer
from src.data_loader import load_all_data, load_competencies, load_labor_functions, load_curriculum
from src.check_data import check_data
from src.check_vectors import check_vectors
from src.check_similarities import check_similarities
from src.download_nltk_data import setup_nltk
from src.data_processor import process_data
from src.schema import init_db, reset_db

def check_dependencies():
    """Проверка и установка необходимых зависимостей"""
    required = {
        'nltk': '3.8.1',
        'scikit-learn': '1.0.0',
        'pandas': '1.3.0',
        'matplotlib': '3.4.0',
        'flask': '2.0.0',
        'pymorphy2': '0.8',
        'pytest': '7.0.0',
        'scipy': '1.7.0',
        'numpy': '1.21.0'
    }
    
    missing = []
    
    for package, min_version in required.items():
        try:
            pkg_resources.require(f"{package}>={min_version}")
        except pkg_resources.VersionConflict:
            print(f"⚠️ {package} версии >={min_version} не установлен")
            missing.append(package)
        except pkg_resources.DistributionNotFound:
            print(f"⚠️ {package} не установлен")
            missing.append(package)
    
    if missing:
        print("\nУстановка отсутствующих зависимостей...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ Зависимости установлены")

def setup_nltk():
    """Загрузка необходимых данных NLTK"""
    import nltk
    required_nltk_data = ['punkt', 'stopwords']
    
    for item in required_nltk_data:
        try:
            nltk.data.find(f'tokenizers/{item}')
        except LookupError:
            print(f"Загрузка {item} для NLTK...")
            nltk.download(item)

def print_top_tfidf_similarities():
    """Выводит топ-3 пар по tfidf_similarity"""
    from src.db import get_db_connection
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT t.title, lf.name, tl.tfidf_similarity, tl.rubert_similarity
        FROM topic_labor_function tl
        JOIN topics t ON t.id = tl.topic_id
        JOIN labor_functions lf ON lf.id = tl.labor_function_id
        ORDER BY tl.tfidf_similarity DESC
        LIMIT 3
    ''')
    print("\nТоп-3 пары тема-функция по tfidf_similarity:")
    for title, name, tfidf_sim, rubert_sim in cursor.fetchall():
        print(f"Тема: {title}\nТрудовая функция: {name}\nTF-IDF similarity: {tfidf_sim:.4f}\nruBERT similarity: {rubert_sim:.4f}\n---")
    conn.close()

def main():
    """Основная функция запуска приложения"""
    parser = argparse.ArgumentParser(description='Обработка и векторизация текстов')
    
    # Группа аргументов для управления БД
    db_group = parser.add_argument_group('Управление базой данных')
    db_group.add_argument('--reset-db', action='store_true', help='Сбросить базу данных')
    db_group.add_argument('--init-db', action='store_true', help='Инициализировать базу данных')
    db_group.add_argument('--load-data', action='store_true', help='Загрузить данные в базу')
    db_group.add_argument('--check-data', action='store_true', help='Проверить загруженные данные')
    
    # Группа аргументов для загрузки конкретных данных
    data_group = parser.add_argument_group('Загрузка конкретных данных')
    data_group.add_argument('--load-competencies', action='store_true', help='Загрузить только компетенции')
    data_group.add_argument('--load-labor-functions', action='store_true', help='Загрузить только трудовые функции')
    data_group.add_argument('--load-curriculum', action='store_true', help='Загрузить только учебные планы')
    
    # Существующие аргументы
    parser.add_argument('--vectorizer', type=str, default='tfidf',
                      help='Тип векторизатора (tfidf или rubert)')
    parser.add_argument('--full-cycle', action='store_true', help='Выполнить полный цикл обработки')
    
    args = parser.parse_args()
    
    # Добавляем путь к src в PYTHONPATH
    src_path = str(Path(__file__).parent)
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    
    try:
        # Проверяем зависимости
        print("Проверка зависимостей...")
        check_dependencies()
        
        # Настраиваем NLTK
        print("\nПроверка данных NLTK...")
        setup_nltk()
        
        if args.full_cycle:
            # Запускаем полный цикл обработки данных
            process_data()
        else:
            # Управление базой данных
            if args.reset_db:
                print("Сброс базы данных...")
                reset_db()
            
            if args.init_db:
                print("Инициализация базы данных...")
                init_db()
            
            # Загрузка данных
            if args.load_data:
                print("Загрузка всех данных...")
                load_all_data()
            else:
                if args.load_competencies:
                    print("Загрузка компетенций...")
                    load_competencies()
                
                if args.load_labor_functions:
                    print("Загрузка трудовых функций...")
                    load_labor_functions()
                
                if args.load_curriculum:
                    print("Загрузка учебных планов...")
                    load_curriculum()
            
            # Проверка данных
            if args.check_data:
                print("Проверка данных...")
                check_data()
            
            # Если не указаны конкретные действия, выполняем полный цикл
            if not any([args.reset_db, args.init_db, args.load_data, args.load_competencies,
                       args.load_labor_functions, args.load_curriculum, args.check_data]):
                # Обработка текстов
                print("Обработка текстов...")
                processor = DatabaseTextProcessor()
                processor.process_all()
                
                # Векторизация
                print(f"Векторизация с использованием {args.vectorizer}...")
                vectorizer = DatabaseVectorizer(vectorizer_type=args.vectorizer)
                vectorizer.vectorize_all()
                
                # Расчет сходства
                print("Расчет сходства между темами и трудовыми функциями...")
                from src.vectorizer import calculate_similarities
                calculate_similarities()
                
                # Проверка векторов
                print("Проверка векторов...")
                check_vectors()
                
                # Проверка сходства
                print("Проверка сходства...")
                check_similarities()
        
    except Exception as e:
        print(f"\n❌ Ошибка: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 