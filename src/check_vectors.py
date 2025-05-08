import sys
import os

# Добавляем корневую директорию в PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
import numpy as np
from src.db import get_db_connection
from src.vectorization_config import VectorizationConfig

def print_vector_info(cursor, table_name, id_field, text_field):
    """Вывод информации о векторах"""
    print(f"\nТаблица {table_name}:\n")
    
    # Получаем первые 5 записей
    if table_name == 'topic_vectors':
        cursor.execute(f"""
            SELECT v.{id_field}, t.title, v.tfidf_vector, v.rubert_vector
            FROM {table_name} v
            JOIN topics t ON t.id = v.{id_field}
            LIMIT 5
        """)
    else:
        cursor.execute(f"""
            SELECT v.{id_field}, t.name, v.tfidf_vector, v.rubert_vector
            FROM {table_name} v
            JOIN labor_functions t ON t.id = v.{id_field}
            LIMIT 5
        """)
    
    for row in cursor.fetchall():
        id_value, text, tfidf_vector, rubert_vector = row
        print(f"ID: {id_value}")
        print(f"Название: {text}")
        
        if tfidf_vector is not None:
            try:
                vector = np.frombuffer(tfidf_vector, dtype=np.float32)
                print(f"Размерность TF-IDF вектора: {vector.shape}")
                print("Пример значений вектора (первые 5):")
                for i in range(min(5, len(vector))):
                    print(f"  Индекс: {i}, Значение: {vector[i]:.4f}")
                print(f"Количество ненулевых элементов: {np.count_nonzero(vector)}")
            except Exception as e:
                print(f"❌ Ошибка при загрузке TF-IDF вектора: {str(e)}")
                print(f"Размер вектора в байтах: {len(tfidf_vector)}")
                print("Первые 10 байт:", ' '.join(f'{b:02x}' for b in tfidf_vector[:10]))
        
        if rubert_vector is not None:
            try:
                vector = np.frombuffer(rubert_vector, dtype=np.float32)
                print(f"Размерность ruBERT вектора: {vector.shape}")
                print("Пример значений вектора (первые 5):")
                for i in range(min(5, len(vector))):
                    print(f"  Индекс: {i}, Значение: {vector[i]:.4f}")
            except Exception as e:
                print(f"❌ Ошибка при загрузке ruBERT вектора: {str(e)}")
                print(f"Размер вектора в байтах: {len(rubert_vector)}")
                print("Первые 10 байт:", ' '.join(f'{b:02x}' for b in rubert_vector[:10]))
        
        print("-" * 50)

def print_vectorization_results(config_id: int):
    """Вывод информации о результатах векторизации"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Получаем информацию о конфигурации
    config = VectorizationConfig(config_id)
    print(f"\nКонфигурация векторизации:")
    print(f"ID: {config.config_id}")
    print(f"Тип: {config.config_type}")
    print(f"Описание: {config.description}")
    
    # Получаем веса
    print("\nВеса:")
    for weight in config.weights:
        print(f"- {weight.entity_type}.{weight.source_type}: {weight.weight}")
        if weight.hours_weight:
            print(f"  Часы: {weight.hours_weight}")
    
    # Получаем результаты векторизации
    cursor.execute("""
        SELECT 
            entity_type,
            COUNT(*) as count,
            AVG(LENGTH(vector_data)) as avg_vector_size
        FROM vectorization_results
        WHERE configuration_id = ?
        GROUP BY entity_type
    """, (config_id,))
    
    print("\nРезультаты векторизации:")
    for entity_type, count, avg_size in cursor.fetchall():
        print(f"- {entity_type}: {count} векторов, средний размер {avg_size:.1f} байт")
    
    # Получаем результаты сходства
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            AVG(similarity_score) as avg_similarity,
            MIN(similarity_score) as min_similarity,
            MAX(similarity_score) as max_similarity
        FROM similarity_results
        WHERE configuration_id = ?
    """, (config_id,))
    
    total, avg_sim, min_sim, max_sim = cursor.fetchone()
    print("\nРезультаты сходства:")
    print(f"- Всего сравнений: {total}")
    print(f"- Среднее сходство: {avg_sim:.3f}")
    print(f"- Минимальное сходство: {min_sim:.3f}")
    print(f"- Максимальное сходство: {max_sim:.3f}")
    
    conn.close()

def check_vectors(config_id=None):
    """Проверка векторов в базе данных"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Получаем все векторы из базы данных
    if config_id is not None:
        cursor.execute("""
            SELECT entity_type, entity_id, vector_type, vector_data
            FROM vectorization_results
            WHERE configuration_id = ?
        """, (config_id,))
    else:
        cursor.execute("""
            SELECT entity_type, entity_id, vector_type, vector_data
            FROM vectorization_results
        """)
    
    results = cursor.fetchall()
    
    if not results:
        print("Векторы не найдены в базе данных")
        return
    
    print(f"Найдено {len(results)} векторов")
    print("=" * 50)
    
    # Группируем векторы по типу и сущности
    for entity_type, entity_id, vector_type, vector_data in results:
        print(f"Тип сущности: {entity_type}")
        print(f"ID сущности: {entity_id}")
        print(f"Тип вектора: {vector_type}")
        
        # Получаем название сущности
        if entity_type == 'lecture_topic':
            cursor.execute("SELECT name FROM lecture_topics WHERE id = ?", (entity_id,))
        elif entity_type == 'practical_topic':
            cursor.execute("SELECT name FROM practical_topics WHERE id = ?", (entity_id,))
        elif entity_type == 'labor_function':
            cursor.execute("SELECT name FROM labor_functions WHERE id = ?", (entity_id,))
        
        name = cursor.fetchone()[0]
        print(f"Название: {name}")
        
        # Анализируем вектор
        vector = np.frombuffer(vector_data, dtype=np.float32)
        print(f"Размерность вектора: {vector.shape}")
        print(f"Норма вектора: {np.linalg.norm(vector):.6f}")
        print("Пример значений (первые 5):")
        for i in range(min(5, len(vector))):
            print(f"  {i}: {vector[i]:.6f}")
        print("-" * 50)
    
    conn.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        config_id = int(sys.argv[1])
        check_vectors(config_id)
    else:
        check_vectors() 