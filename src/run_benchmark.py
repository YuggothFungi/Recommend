#!/usr/bin/env python3
"""
Скрипт для запуска бенчмарка векторизации
"""

import sys
import os
from pathlib import Path

# Добавляем корневую директорию проекта в PYTHONPATH
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

import argparse
from src.vectorization_benchmark import VectorizationBenchmark
import logging

def main():
    """Основная функция запуска бенчмарка"""
    parser = argparse.ArgumentParser(description='Бенчмарк методов векторизации')
    parser.add_argument('--config-id', type=int, default=3,
                      help='ID конфигурации векторизации (по умолчанию: 3)')
    args = parser.parse_args()
    
    # Настройка логирования
    logging.basicConfig(level=logging.INFO)
    
    # Создаем и запускаем бенчмарк
    benchmark = VectorizationBenchmark(args.config_id)
    results = benchmark.run_benchmark()
    benchmark.print_results(results)

if __name__ == '__main__':
    main() 