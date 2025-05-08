import sqlite3
import os

def check_similarity_stats():
    db_path = os.path.join('database', 'database.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Проверяем количество результатов сходства
    cursor.execute("SELECT COUNT(*) FROM similarity_results WHERE configuration_id = 1")
    total_count = cursor.fetchone()[0]
    print(f'Количество результатов сходства: {total_count}')
    
    # Статистика по типам тем
    for topic_type in ['lecture', 'practical']:
        print(f"\nТип темы: {topic_type}")
        print("=" * 80)
        
        # Общая статистика для ruBERT
        cursor.execute("""
            SELECT COUNT(*), 
                   COUNT(CASE WHEN rubert_similarity > 0 THEN 1 END),
                   AVG(rubert_similarity),
                   MIN(rubert_similarity),
                   MAX(rubert_similarity)
            FROM similarity_results 
            WHERE configuration_id = 1 AND topic_type = ?
        """, (topic_type,))
        
        total, non_zero, avg, min_sim, max_sim = cursor.fetchone()
        print(f"\nСтатистика ruBERT:")
        print(f"Всего сравнений: {total}")
        print(f"Ненулевых сходств: {non_zero}")
        print(f"Среднее сходство: {avg:.4f}")
        print(f"Минимальное сходство: {min_sim:.4f}")
        print(f"Максимальное сходство: {max_sim:.4f}")
        
        # Общая статистика для TF-IDF
        cursor.execute("""
            SELECT COUNT(*), 
                   COUNT(CASE WHEN tfidf_similarity > 0 THEN 1 END),
                   AVG(tfidf_similarity),
                   MIN(tfidf_similarity),
                   MAX(tfidf_similarity)
            FROM similarity_results 
            WHERE configuration_id = 1 AND topic_type = ?
        """, (topic_type,))
        
        total, non_zero, avg, min_sim, max_sim = cursor.fetchone()
        print(f"\nСтатистика TF-IDF:")
        print(f"Всего сравнений: {total}")
        print(f"Ненулевых сходств: {non_zero}")
        print(f"Среднее сходство: {avg:.4f}")
        print(f"Минимальное сходство: {min_sim:.4f}")
        print(f"Максимальное сходство: {max_sim:.4f}")
        
        # Топ-5 наиболее похожих пар для ruBERT
        print(f"\nТоп-5 наиболее похожих пар (ruBERT):")
        print("=" * 80)
        
        # Получаем информацию о темах и трудовых функциях
        if topic_type == 'lecture':
            cursor.execute("""
                SELECT DISTINCT lt.name as topic_name,
                       lf.name as function_name,
                       MAX(sr.rubert_similarity) as similarity,
                       MAX(sr.tfidf_similarity) as tfidf_similarity
                FROM similarity_results sr
                JOIN lecture_topics lt ON lt.id = sr.topic_id
                JOIN labor_functions lf ON lf.id = sr.labor_function_id
                WHERE sr.configuration_id = 1 
                AND sr.topic_type = ?
                GROUP BY lt.name, lf.name
                ORDER BY similarity DESC
                LIMIT 5
            """, (topic_type,))
        else:
            cursor.execute("""
                SELECT DISTINCT pt.name as topic_name,
                       lf.name as function_name,
                       MAX(sr.rubert_similarity) as similarity,
                       MAX(sr.tfidf_similarity) as tfidf_similarity
                FROM similarity_results sr
                JOIN practical_topics pt ON pt.id = sr.topic_id
                JOIN labor_functions lf ON lf.id = sr.labor_function_id
                WHERE sr.configuration_id = 1 
                AND sr.topic_type = ?
                GROUP BY pt.name, lf.name
                ORDER BY similarity DESC
                LIMIT 5
            """, (topic_type,))
        
        for topic_name, function_name, similarity, tfidf_similarity in cursor.fetchall():
            print(f"\nТема: {topic_name}")
            print(f"Трудовая функция: {function_name}")
            print(f"ruBERT сходство: {similarity:.4f}")
            print(f"TF-IDF сходство: {tfidf_similarity:.4f}")
        
        # Топ-5 наиболее похожих пар для TF-IDF
        print(f"\nТоп-5 наиболее похожих пар (TF-IDF):")
        print("=" * 80)
        
        if topic_type == 'lecture':
            cursor.execute("""
                SELECT DISTINCT lt.name as topic_name,
                       lf.name as function_name,
                       MAX(sr.rubert_similarity) as rubert_similarity,
                       MAX(sr.tfidf_similarity) as similarity
                FROM similarity_results sr
                JOIN lecture_topics lt ON lt.id = sr.topic_id
                JOIN labor_functions lf ON lf.id = sr.labor_function_id
                WHERE sr.configuration_id = 1 
                AND sr.topic_type = ?
                GROUP BY lt.name, lf.name
                ORDER BY similarity DESC
                LIMIT 5
            """, (topic_type,))
        else:
            cursor.execute("""
                SELECT DISTINCT pt.name as topic_name,
                       lf.name as function_name,
                       MAX(sr.rubert_similarity) as rubert_similarity,
                       MAX(sr.tfidf_similarity) as similarity
                FROM similarity_results sr
                JOIN practical_topics pt ON pt.id = sr.topic_id
                JOIN labor_functions lf ON lf.id = sr.labor_function_id
                WHERE sr.configuration_id = 1 
                AND sr.topic_type = ?
                GROUP BY pt.name, lf.name
                ORDER BY similarity DESC
                LIMIT 5
            """, (topic_type,))
        
        for topic_name, function_name, rubert_similarity, similarity in cursor.fetchall():
            print(f"\nТема: {topic_name}")
            print(f"Трудовая функция: {function_name}")
            print(f"ruBERT сходство: {rubert_similarity:.4f}")
            print(f"TF-IDF сходство: {similarity:.4f}")
    
    conn.close()

if __name__ == '__main__':
    check_similarity_stats() 