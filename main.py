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
from src.vectorizer import Vectorizer
from src.data_loader import load_all_data, load_competencies, load_labor_functions, load_curriculum
from src.check_data import check_data
from src.check_vectors import check_vectors
from src.check_similarities import check_similarities
from src.check_normalized_texts import check_normalized_texts
from src.download_nltk_data import setup_nltk
from src.data_processor import process_data
from src.schema import init_db, reset_db
from src.vectorization_config import VectorizationConfig
from src.check_db import check_database
import os
import logging

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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
        'numpy': '1.21.0',
        'torch': '1.9.0',
        'transformers': '4.5.0'
    }
    
    missing = []
    
    for package, min_version in required.items():
        try:
            pkg_resources.require(f"{package}>={min_version}")
        except pkg_resources.VersionConflict:
            logger.warning(f"⚠️ {package} версии >={min_version} не установлен")
            missing.append(package)
        except pkg_resources.DistributionNotFound:
            logger.warning(f"⚠️ {package} не установлен")
            missing.append(package)
    
    if missing:
        logger.info("\nУстановка отсутствующих зависимостей...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        logger.info("✓ Зависимости установлены")

def print_vectorization_configs():
    """Выводит список доступных конфигураций векторизации"""
    configs = VectorizationConfig.get_available_configs()
    logger.info("\nДоступные конфигурации векторизации:")
    for config in configs:
        logger.info(f"\nID: {config.config_id}")
        logger.info(f"Тип: {config.config_type}")
        logger.info(f"Описание: {config.description}")
        logger.info("Веса:")
        for weight in config.weights:
            logger.info(f"  - {weight.entity_type}.{weight.source_type}: {weight.weight}")
            if weight.hours_weight:
                logger.info(f"    Часы: {weight.hours_weight}")

def main():
    """Основная функция запуска приложения"""
    parser = argparse.ArgumentParser(description='Обработка данных для системы рекомендаций')
    
    # Группа аргументов для управления базой данных
    db_group = parser.add_argument_group('Управление базой данных')
    db_group.add_argument('--reset-db', action='store_true', help='Сбросить базу данных')
    db_group.add_argument('--init-db', action='store_true', help='Инициализировать базу данных')
    
    # Группа аргументов для загрузки данных
    data_group = parser.add_argument_group('Загрузка данных')
    data_group.add_argument('--load-data', action='store_true', help='Загрузить все данные')
    data_group.add_argument('--load-competencies', action='store_true', help='Загрузить компетенции')
    data_group.add_argument('--load-labor-functions', action='store_true', help='Загрузить трудовые функции')
    data_group.add_argument('--load-curriculum', action='store_true', help='Загрузить учебный план')
    
    # Группа аргументов для проверки данных
    check_group = parser.add_argument_group('Проверка данных')
    check_group.add_argument('--check-data', action='store_true', help='Проверить загруженные данные')
    check_group.add_argument('--check-data-extended', action='store_true', help='Расширенная проверка данных')
    
    # Группа аргументов для обработки текстов
    text_group = parser.add_argument_group('Обработка текстов')
    text_group.add_argument('--normalize-texts', action='store_true', help='Нормализовать все текстовые поля в базе данных')
    text_group.add_argument('--check-texts', action='store_true', help='Проверить нормализацию текстов')
    
    # Группа аргументов для векторизации
    vectorization_group = parser.add_argument_group('Векторизация')
    vectorization_group.add_argument('--vectorizer', type=str, default='tfidf',
                      help='Тип векторизатора (tfidf или rubert)')
    vectorization_group.add_argument('--config-id', type=int, help='ID конфигурации векторизации')
    vectorization_group.add_argument('--list-configs', action='store_true', help='Показать список доступных конфигураций')
    vectorization_group.add_argument('--check-vectors', type=int, help='Проверить векторы для указанной конфигурации')
    
    # Группа аргументов для веб-интерфейса
    web_group = parser.add_argument_group('Веб-интерфейс')
    web_group.add_argument('--web', action='store_true', help='Запустить веб-сервер')
    web_group.add_argument('--port', type=int, default=5000, help='Порт для веб-сервера (по умолчанию: 5000)')
    web_group.add_argument('--host', type=str, default='0.0.0.0', help='Хост для веб-сервера (по умолчанию: 0.0.0.0)')
    
    # Существующие аргументы
    parser.add_argument('--full-cycle', action='store_true', help='Выполнить полный цикл обработки')
    
    args = parser.parse_args()
    
    # Добавляем корневую директорию в PYTHONPATH
    root_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(root_dir)
    
    try:
        # Проверяем зависимости
        logger.info("Проверка зависимостей...")
        check_dependencies()
        
        # Настраиваем NLTK
        logger.info("\nПроверка данных NLTK...")
        setup_nltk()
        
        # Запуск веб-сервера
        if args.web:
            logger.info("Проверка базы данных перед запуском веб-сервера...")
            if not check_database():
                logger.error("База данных не готова. Пожалуйста, инициализируйте базу данных и загрузите данные.")
                logger.info("Используйте следующие команды:")
                logger.info("python main.py --init-db")
                logger.info("python main.py --load-data")
                sys.exit(1)
            
            logger.info(f"Запуск веб-сервера на {args.host}:{args.port}...")
            from frontend.app import app
            app.run(host=args.host, port=args.port, debug=True)
            return
        
        # Показываем список конфигураций
        if args.list_configs:
            print_vectorization_configs()
            return
        
        # Проверяем векторы
        if args.check_vectors:
            logger.info(f"Проверка векторов для конфигурации {args.check_vectors}...")
            check_vectors(args.check_vectors)
            return
        
        if args.full_cycle:
            # Запускаем полный цикл обработки данных
            process_data()
            return
        
        # Сброс базы данных
        if args.reset_db:
            logger.info("Сброс базы данных...")
            reset_db()
            logger.info("База данных успешно сброшена")
        
        # Инициализация базы данных
        if args.init_db:
            logger.info("Инициализация базы данных...")
            init_db()
            logger.info("База данных успешно инициализирована")
        
        # Загрузка данных
        if args.load_data:
            logger.info("Загрузка данных...")
            load_all_data()
            logger.info("Данные успешно загружены")
        elif args.load_competencies:
            logger.info("Загрузка компетенций...")
            load_competencies()
            logger.info("Компетенции успешно загружены")
        elif args.load_labor_functions:
            logger.info("Загрузка трудовых функций...")
            load_labor_functions()
            logger.info("Трудовые функции успешно загружены")
        elif args.load_curriculum:
            logger.info("Загрузка учебного плана...")
            load_curriculum()
            logger.info("Учебный план успешно загружен")
        
        # Проверка данных
        if args.check_data:
            logger.info("Проверка данных...")
            check_data()
        elif args.check_data_extended:
            logger.info("Расширенная проверка данных...")
            from src.db import get_db_connection
            conn = get_db_connection()
            try:
                check_data(conn, extended=True)
            finally:
                conn.close()
        
        # Нормализация текстов
        if args.normalize_texts:
            logger.info("Нормализация текстов...")
            processor = DatabaseTextProcessor()
            processor.process_all()
            logger.info("Нормализация текстов завершена")
        
        # Проверка нормализации текстов
        if args.check_texts:
            logger.info("Проверка нормализации текстов...")
            from src.db import get_db_connection
            conn = get_db_connection()
            try:
                check_normalized_texts(conn)
            finally:
                conn.close()
        
        # Если не указаны конкретные действия, выполняем полный цикл
        if not any([args.reset_db, args.init_db, args.load_data, args.load_competencies,
                   args.load_labor_functions, args.load_curriculum, args.check_data,
                   args.check_data_extended, args.normalize_texts, args.check_texts]):
            # Обработка текстов
            logger.info("Обработка текстов...")
            processor = DatabaseTextProcessor()
            processor.process_all()
            
            # Векторизация
            if args.config_id:
                logger.info(f"Векторизация с использованием конфигурации {args.config_id} и алгоритма {args.vectorizer}...")
                config = VectorizationConfig(args.config_id)
                config.vectorizer_type = args.vectorizer
                vectorizer = Vectorizer(config=config, vectorizer_type=args.vectorizer)
            else:
                logger.info(f"Векторизация с использованием {args.vectorizer}...")
                vectorizer = Vectorizer(vectorizer_type=args.vectorizer)
            
            vectorizer.vectorize_all()
            
            # Расчет сходства
            logger.info("Расчет сходства между темами и трудовыми функциями...")
            from src.vectorizer import calculate_similarities
            calculate_similarities(config)
    
    except Exception as e:
        logger.error(f"Ошибка: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 