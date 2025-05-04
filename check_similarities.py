import sqlite3
import numpy as np

def check_similarities():
    """Проверка значений сходства в базе данных"""
    conn = sqlite3.connect('database/database.db')
    cursor = conn.cursor()
    
    # Проверяем количество записей
    cursor.execute("SELECT COUNT(*) FROM topic_labor_function")
    count = cursor.fetchone()[0]
    print(f"\nВсего записей в таблице topic_labor_function: {count}")
    
    # Проверяем минимальные и максимальные значения сходства
    cursor.execute("""
        SELECT 
            MIN(tfidf_similarity) as min_tfidf,
            MAX(tfidf_similarity) as max_tfidf,
            MIN(rubert_similarity) as min_rubert,
            MAX(rubert_similarity) as max_rubert
        FROM topic_labor_function
    """)
    min_tfidf, max_tfidf, min_rubert, max_rubert = cursor.fetchone()
    print(f"\nTF-IDF сходство:")
    print(f"Минимальное: {min_tfidf:.3f}")
    print(f"Максимальное: {max_tfidf:.3f}")
    print(f"\nruBERT сходство:")
    print(f"Минимальное: {min_rubert:.3f}")
    print(f"Максимальное: {max_rubert:.3f}")
    
    # Проверяем распределение значений TF-IDF сходства
    print("\nРаспределение значений TF-IDF сходства:")
    ranges = [(0, 0), (0, 0.1), (0.1, 0.2), (0.2, 0.3), (0.3, 0.4), 
             (0.4, 0.5), (0.5, 0.6), (0.6, 0.7), (0.7, 0.8), (0.8, 0.9), (0.9, 1.0)]
    
    for start, end in ranges:
        if start == 0 and end == 0:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM topic_labor_function 
                WHERE tfidf_similarity = 0
            """)
        else:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM topic_labor_function 
                WHERE tfidf_similarity > ? AND tfidf_similarity <= ?
            """, (start, end))
        count = cursor.fetchone()[0]
        if start == 0 and end == 0:
            print(f"Равно 0: {count}")
        else:
            print(f"{start:.1f}-{end:.1f}: {count}")
    
    # Проверяем несколько конкретных записей
    print("\nПримеры записей:")
    cursor.execute("""
        SELECT topic_id, labor_function_id, tfidf_similarity, rubert_similarity
        FROM topic_labor_function
        LIMIT 5
    """)
    for row in cursor.fetchall():
        print(f"Тема {row[0]} - Функция {row[1]}: TF-IDF={row[2]:.3f}, ruBERT={row[3]:.3f}")
    
    conn.close()

if __name__ == '__main__':
    check_similarities() 