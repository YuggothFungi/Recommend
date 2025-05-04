import pickle
import numpy as np
from src.db import get_db_connection

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