from src.db import get_db_connection

def print_normalized_texts(cursor, table_name, original_field, normalized_field):
    """Выводит оригинальные и нормализованные тексты из указанной таблицы"""
    cursor.execute(f"""
        SELECT {original_field}, {normalized_field}
        FROM {table_name} 
        WHERE {normalized_field} IS NOT NULL 
        LIMIT 3
    """)
    rows = cursor.fetchall()
    
    print(f"\nТаблица {table_name}:")
    for row in rows:
        print("\nОригинальный текст:")
        print(row[0])
        print("\nНормализованный текст:")
        print(row[1])
        print("-" * 50)

def check_normalized_texts():
    """Проверка нормализованных текстов"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Проверяем нормализованные тексты в разных таблицах
    print_normalized_texts(cursor, 'topics', 'title', 'nltk_normalized_title')
    print_normalized_texts(cursor, 'competencies', 'description', 'nltk_normalized_description')
    print_normalized_texts(cursor, 'labor_functions', 'name', 'nltk_normalized_name')
    print_normalized_texts(cursor, 'labor_components', 'description', 'nltk_normalized_description')
    
    conn.close()

if __name__ == "__main__":
    check_normalized_texts() 