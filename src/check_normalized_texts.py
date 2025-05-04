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

def check_normalized_texts(conn):
    """Проверка наличия нормализованных текстов"""
    cursor = conn.cursor()
    
    # Проверяем темы
    cursor.execute("""
        SELECT COUNT(*) 
        FROM topics 
        WHERE nltk_normalized_title IS NULL 
        OR nltk_normalized_description IS NULL
    """)
    unnormalized_topics = cursor.fetchone()[0]
    if unnormalized_topics > 0:
        raise ValueError(f"Есть {unnormalized_topics} ненормализованных текстов в таблице topics")
    
    # Проверяем трудовые функции
    cursor.execute("""
        SELECT COUNT(*) 
        FROM labor_functions 
        WHERE nltk_normalized_name IS NULL
    """)
    unnormalized_functions = cursor.fetchone()[0]
    if unnormalized_functions > 0:
        raise ValueError(f"Есть {unnormalized_functions} ненормализованных текстов в таблице labor_functions")
    
    # Проверяем компоненты
    cursor.execute("""
        SELECT COUNT(*) 
        FROM labor_components 
        WHERE nltk_normalized_description IS NULL
    """)
    unnormalized_components = cursor.fetchone()[0]
    if unnormalized_components > 0:
        raise ValueError(f"Есть {unnormalized_components} ненормализованных текстов в таблице labor_components")
    
    print("Все тексты нормализованы")

if __name__ == "__main__":
    conn = get_db_connection()
    check_normalized_texts(conn) 