#!/usr/bin/env python3
"""
Главный файл запуска приложения.
Проверяет зависимости и запускает основную логику из src/main.py
"""

import sys
import pkg_resources
import subprocess
from pathlib import Path

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

def main():
    """Основная функция запуска приложения"""
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
        
        # Импортируем и запускаем основную логику
        print("\nЗапуск основной логики приложения...")
        from src.main import main as app_main
        app_main()
        
    except Exception as e:
        print(f"\n❌ Ошибка: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 