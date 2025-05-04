import sqlite3
import numpy as np

def check_vectors():
    """Проверка векторов в базе данных"""
    conn = sqlite3.connect('database/database.db')
    cursor = conn.cursor()
    
    # Проверяем векторы тем
    cursor.execute("""
        SELECT topic_id, tfidf_vector
        FROM topic_vectors
        LIMIT 1
    """)
    topic_row = cursor.fetchone()
    if topic_row and topic_row[1]:
        topic_vector = np.frombuffer(topic_row[1], dtype=np.float32)
        print(f"\nВектор темы {topic_row[0]}:")
        print(f"Размер: {topic_vector.shape}")
        print(f"Тип: {topic_vector.dtype}")
        print(f"Сумма: {np.sum(topic_vector)}")
        print(f"Среднее: {np.mean(topic_vector)}")
        print(f"Мин: {np.min(topic_vector)}")
        print(f"Макс: {np.max(topic_vector)}")
        print(f"Количество ненулевых элементов: {np.count_nonzero(topic_vector)}")
    else:
        print("\nВекторы тем не найдены")
    
    # Проверяем векторы трудовых функций
    cursor.execute("""
        SELECT labor_function_id, tfidf_vector
        FROM labor_function_vectors
        WHERE tfidf_vector IS NOT NULL
        LIMIT 1
    """)
    function_row = cursor.fetchone()
    if function_row and function_row[1]:
        function_vector = np.frombuffer(function_row[1], dtype=np.float32)
        print(f"\nВектор трудовой функции {function_row[0]}:")
        print(f"Размер: {function_vector.shape}")
        print(f"Тип: {function_vector.dtype}")
        print(f"Сумма: {np.sum(function_vector)}")
        print(f"Среднее: {np.mean(function_vector)}")
        print(f"Мин: {np.min(function_vector)}")
        print(f"Макс: {np.max(function_vector)}")
        print(f"Количество ненулевых элементов: {np.count_nonzero(function_vector)}")
        
        # Проверяем косинусное сходство
        if topic_row and topic_row[1]:
            # Нормализуем векторы
            topic_vector = topic_vector / np.linalg.norm(topic_vector)
            function_vector = function_vector / np.linalg.norm(function_vector)
            
            similarity = np.dot(topic_vector, function_vector)
            print(f"\nКосинусное сходство между векторами: {similarity:.3f}")
    else:
        print("\nВекторы трудовых функций не найдены")
    
    conn.close()

if __name__ == '__main__':
    check_vectors() 