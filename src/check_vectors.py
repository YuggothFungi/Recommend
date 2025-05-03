import pickle
import numpy as np
from db import get_db_connection

def print_vector_info(cursor, table_name, id_field, name_field):
    """Выводит информацию о векторах из указанной таблицы"""
    cursor.execute(f"""
        SELECT v.{id_field}, {name_field}, v.vector
        FROM {table_name} v
        JOIN {table_name.split('_vectors')[0]}s t ON v.{id_field} = t.id
        LIMIT 5
    """)
    rows = cursor.fetchall()
    
    print(f"\nТаблица {table_name}:")
    for row in rows:
        id_value, name, vector_bytes = row
        vector = pickle.loads(vector_bytes)
        
        print(f"\nID: {id_value}")
        print(f"Название: {name}")
        print(f"Размерность вектора: {vector.shape}")
        print(f"Количество ненулевых элементов: {vector.nnz}")
        print(f"Пример ненулевых элементов (первые 5):")
        nonzero_indices = vector.nonzero()[1][:5]
        nonzero_values = vector.data[:5]
        for idx, val in zip(nonzero_indices, nonzero_values):
            print(f"  Индекс: {idx}, Значение: {val:.4f}")
        print("-" * 50)

def check_vectors():
    """Проверка векторов"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Проверяем векторы тем
    print_vector_info(cursor, 'topic_vectors', 'topic_id', 't.title')
    
    # Проверяем векторы трудовых функций
    print_vector_info(cursor, 'labor_function_vectors', 'labor_function_id', 't.name')
    
    conn.close()

if __name__ == "__main__":
    check_vectors() 