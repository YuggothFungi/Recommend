import sqlite3
import os

def check_results():
    db_path = os.path.join('database', 'database.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Проверяем количество результатов сходства
    cursor.execute("SELECT COUNT(*) FROM similarity_results WHERE configuration_id = 1")
    total_count = cursor.fetchone()[0]
    print(f'Количество результатов сходства: {total_count}')
    
    # Проверяем количество ненулевых TF-IDF сходств
    cursor.execute("SELECT COUNT(*) FROM similarity_results WHERE configuration_id = 1 AND tfidf_similarity > 0")
    tfidf_count = cursor.fetchone()[0]
    print(f'Количество ненулевых TF-IDF сходств: {tfidf_count}')
    
    # Проверяем максимальное и минимальное значение TF-IDF сходства
    cursor.execute("SELECT MIN(tfidf_similarity), MAX(tfidf_similarity) FROM similarity_results WHERE configuration_id = 1")
    min_sim, max_sim = cursor.fetchone()
    print(f'Минимальное TF-IDF сходство: {min_sim}')
    print(f'Максимальное TF-IDF сходство: {max_sim}')
    
    # Проверяем количество векторизованных сущностей
    cursor.execute("SELECT entity_type, COUNT(*) FROM vectorization_results WHERE configuration_id = 1 GROUP BY entity_type")
    for entity_type, count in cursor.fetchall():
        print(f'Количество векторизованных {entity_type}: {count}')
    
    conn.close()

if __name__ == '__main__':
    check_results() 