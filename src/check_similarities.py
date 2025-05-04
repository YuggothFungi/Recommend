from src.db import get_db_connection
import numpy as np

def print_similarity_stats(cursor):
    """Вывод статистики по сходству"""
    # Общая статистика
    cursor.execute("SELECT COUNT(*) FROM topic_labor_function")
    total_pairs = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM topic_labor_function WHERE tfidf_similarity > 0")
    tfidf_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM topic_labor_function WHERE rubert_similarity > 0")
    rubert_count = cursor.fetchone()[0]
    
    print("\nСтатистика сходства:")
    print(f"Всего пар: {total_pairs}")
    print(f"Пар с ненулевым TF-IDF сходством: {tfidf_count}")
    print(f"Пар с ненулевым ruBERT сходством: {rubert_count}")
    
    # Средние значения
    cursor.execute("SELECT AVG(tfidf_similarity), AVG(rubert_similarity) FROM topic_labor_function")
    avg_tfidf, avg_rubert = cursor.fetchone()
    print(f"\nСредние значения:")
    print(f"Среднее TF-IDF сходство: {avg_tfidf:.4f}")
    print(f"Среднее ruBERT сходство: {avg_rubert:.4f}")

def print_top_similarities(cursor, limit=3):
    """Вывод топ-N пар по сходству"""
    # Топ по TF-IDF
    cursor.execute('''
        SELECT t.title, lf.name, tl.tfidf_similarity, tl.rubert_similarity
        FROM topic_labor_function tl
        JOIN topics t ON t.id = tl.topic_id
        JOIN labor_functions lf ON lf.id = tl.labor_function_id
        ORDER BY tl.tfidf_similarity DESC
        LIMIT ?
    ''', (limit,))
    
    print(f"\nТоп-{limit} пары по TF-IDF сходству:")
    for title, name, tfidf_sim, rubert_sim in cursor.fetchall():
        print(f"Тема: {title}")
        print(f"Трудовая функция: {name}")
        print(f"TF-IDF similarity: {tfidf_sim:.4f}")
        print(f"ruBERT similarity: {rubert_sim:.4f}")
        print("---")
    
    # Топ по ruBERT
    cursor.execute('''
        SELECT t.title, lf.name, tl.tfidf_similarity, tl.rubert_similarity
        FROM topic_labor_function tl
        JOIN topics t ON t.id = tl.topic_id
        JOIN labor_functions lf ON lf.id = tl.labor_function_id
        ORDER BY tl.rubert_similarity DESC
        LIMIT ?
    ''', (limit,))
    
    print(f"\nТоп-{limit} пары по ruBERT сходству:")
    for title, name, tfidf_sim, rubert_sim in cursor.fetchall():
        print(f"Тема: {title}")
        print(f"Трудовая функция: {name}")
        print(f"TF-IDF similarity: {tfidf_sim:.4f}")
        print(f"ruBERT similarity: {rubert_sim:.4f}")
        print("---")

def check_similarities():
    """Проверка сходства между темами и трудовыми функциями"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Проверяем существование таблицы
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='topic_labor_function'
    """)
    if not cursor.fetchone():
        print("❌ Таблица topic_labor_function не существует")
        conn.close()
        return
    
    # Выводим статистику
    print_similarity_stats(cursor)
    
    # Выводим топ-3 пары
    print_top_similarities(cursor)
    
    conn.close()

if __name__ == "__main__":
    check_similarities() 