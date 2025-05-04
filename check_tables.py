import sqlite3

def check_tables():
    """Проверка таблиц в базе данных"""
    conn = sqlite3.connect('database/database.db')
    cursor = conn.cursor()
    
    # Получаем список всех таблиц
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table'
    """)
    tables = cursor.fetchall()
    print("\nСписок таблиц в базе данных:")
    for table in tables:
        print(f"- {table[0]}")
        
        # Получаем структуру таблицы
        cursor.execute(f"PRAGMA table_info({table[0]})")
        columns = cursor.fetchall()
        print("  Колонки:")
        for col in columns:
            print(f"    {col[1]} ({col[2]})")
            
        # Получаем количество записей
        cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
        count = cursor.fetchone()[0]
        print(f"  Количество записей: {count}")
        
        # Если это таблица с векторами, проверяем количество ненулевых векторов
        if table[0] in ['topic_vectors', 'labor_function_vectors']:
            cursor.execute(f"""
                SELECT COUNT(*) 
                FROM {table[0]} 
                WHERE tfidf_vector IS NOT NULL
            """)
            vector_count = cursor.fetchone()[0]
            print(f"  Количество ненулевых TF-IDF векторов: {vector_count}")
            
            cursor.execute(f"""
                SELECT COUNT(*) 
                FROM {table[0]} 
                WHERE rubert_vector IS NOT NULL
            """)
            vector_count = cursor.fetchone()[0]
            print(f"  Количество ненулевых ruBERT векторов: {vector_count}")
        print()
    
    conn.close()

if __name__ == '__main__':
    check_tables() 