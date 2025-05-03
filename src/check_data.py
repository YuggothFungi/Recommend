from src.db import get_db_connection

def print_table_info(cursor, table_name):
    """Выводит информацию о количестве записей в таблице и первые несколько строк"""
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    print(f"\nТаблица {table_name}:")
    print(f"Всего записей: {count}")
    
    cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
    rows = cursor.fetchall()
    if rows:
        # Получаем имена столбцов
        columns = [description[0] for description in cursor.description]
        print("\nПервые 3 записи:")
        for row in rows:
            print("---")
            for col, val in zip(columns, row):
                print(f"{col}: {val}")

def check_data():
    """Проверка загруженных данных"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Проверяем все таблицы
    tables = [
        'topics',
        'competencies',
        'labor_functions',
        'component_types',
        'labor_components',
        'labor_function_components',
        'topic_competency',
        'topic_labor_function'
    ]
    
    for table in tables:
        print_table_info(cursor, table)
    
    conn.close()

if __name__ == "__main__":
    check_data() 