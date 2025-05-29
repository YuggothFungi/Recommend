import sqlite3
import os

def check_db_structure():
    db_path = os.path.join('database', 'database.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Получаем список всех таблиц
    cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
    tables = cursor.fetchall()
    
    print('Таблицы в базе данных:')
    for table in tables:
        print(f'- {table[0]}')
        # Получаем структуру таблицы
        cursor.execute(f'PRAGMA table_info({table[0]})')
        columns = cursor.fetchall()
        for col in columns:
            print(f'  * {col[1]} ({col[2]})')
    
    conn.close()

if __name__ == "__main__":
    check_db_structure() 