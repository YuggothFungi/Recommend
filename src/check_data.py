from src.db import get_db_connection

def print_table_info(cursor, table_name):
    """Выводит информацию о количестве записей в таблице и первые несколько строк"""
    # Получаем информацию о столбцах таблицы
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    
    # Определяем, есть ли столбец id
    has_id = any(col[1] == 'id' for col in columns)
    
    # Формируем запрос в зависимости от наличия столбца id
    if has_id:
        cursor.execute(f"SELECT COUNT(DISTINCT id) FROM {table_name}")
    else:
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

def print_table_count(cursor, table_name):
    """Выводит только количество записей в таблице"""
    # Получаем информацию о столбцах таблицы
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    
    # Определяем, есть ли столбец id
    has_id = any(col[1] == 'id' for col in columns)
    
    # Формируем запрос в зависимости от наличия столбца id
    if has_id:
        cursor.execute(f"SELECT COUNT(DISTINCT id) FROM {table_name}")
    else:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    
    count = cursor.fetchone()[0]
    print(f"{table_name}: {count} записей")

def check_relationships(cursor):
    """Проверяет корректность связей между таблицами"""
    print("\nПроверка связей между таблицами:")
    
    # Проверка дисциплин и их компетенций
    cursor.execute("""
        SELECT d.name, COUNT(dc.competency_id) as comp_count
        FROM disciplines d
        LEFT JOIN discipline_competencies dc ON d.id = dc.discipline_id
        GROUP BY d.id
    """)
    print("\nКоличество компетенций по дисциплинам:")
    for row in cursor.fetchall():
        print(f"{row[0]}: {row[1]} компетенций")
    
    # Проверка разделов и их тем
    cursor.execute("""
        SELECT d.name, s.name as section_name, 
               COUNT(DISTINCT lt.id) as lecture_count,
               COUNT(DISTINCT pt.id) as practical_count,
               COUNT(DISTINCT scq.id) as questions_count
        FROM disciplines d
        JOIN sections s ON d.id = s.discipline_id
        LEFT JOIN lecture_topics lt ON s.id = lt.section_id
        LEFT JOIN practical_topics pt ON s.id = pt.section_id
        LEFT JOIN self_control_questions scq ON s.id = scq.section_id
        GROUP BY s.id
    """)
    print("\nКоличество тем и вопросов по разделам:")
    for row in cursor.fetchall():
        print(f"Дисциплина: {row[0]}")
        print(f"Раздел: {row[1]}")
        print(f"- Лекций: {row[2]}")
        print(f"- Практических: {row[3]}")
        print(f"- Вопросов: {row[4]}")
    
    # Проверка трудовых функций и их компонентов
    cursor.execute("""
        SELECT lf.name, 
               COUNT(DISTINCT CASE WHEN lc.component_type_id = 1 THEN lc.id END) as actions,
               COUNT(DISTINCT CASE WHEN lc.component_type_id = 2 THEN lc.id END) as skills,
               COUNT(DISTINCT CASE WHEN lc.component_type_id = 3 THEN lc.id END) as knowledge,
               COUNT(DISTINCT CASE WHEN lc.component_type_id = 4 THEN lc.id END) as other
        FROM labor_functions lf
        LEFT JOIN labor_components lc ON lf.id = lc.labor_function_id
        GROUP BY lf.id
    """)
    print("\nКоличество компонентов по трудовым функциям:")
    for row in cursor.fetchall():
        print(f"Трудовая функция: {row[0]}")
        print(f"- Действий: {row[1]}")
        print(f"- Умений: {row[2]}")
        print(f"- Знаний: {row[3]}")
        print(f"- Других характеристик: {row[4]}")

def check_data_basic():
    """Проверка загруженных данных - только количество записей"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Проверяем основные таблицы
    main_tables = [
        'disciplines',
        'semesters',
        'sections',
        'lecture_topics',
        'practical_topics',
        'self_control_questions',
        'competencies',
        'specialties',
        'labor_functions',
        'labor_components'
    ]
    
    print("Количество записей в основных таблицах:")
    for table in main_tables:
        print_table_count(cursor, table)
    
    # Проверяем таблицы связей
    relation_tables = [
        'discipline_semesters',
        'discipline_competencies',
        'specialty_labor_functions'
    ]
    
    print("\nКоличество записей в таблицах связей:")
    for table in relation_tables:
        print_table_count(cursor, table)
    
    conn.close()

def check_data(extended=False):
    """Проверка загруженных данных
    
    Args:
        extended (bool): Если True, выводит расширенную информацию о данных
    """
    if not extended:
        check_data_basic()
        return
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Проверяем основные таблицы
    main_tables = [
        'disciplines',
        'semesters',
        'sections',
        'lecture_topics',
        'practical_topics',
        'self_control_questions',
        'competencies',
        'specialties',
        'labor_functions',
        'labor_components'
    ]
    
    print("Проверка основных таблиц:")
    for table in main_tables:
        print_table_info(cursor, table)
    
    # Проверяем таблицы связей
    relation_tables = [
        'discipline_semesters',
        'discipline_competencies',
        'specialty_labor_functions'
    ]
    
    print("\nПроверка таблиц связей:")
    for table in relation_tables:
        print_table_info(cursor, table)
    
    # Проверяем корректность связей
    check_relationships(cursor)
    
    conn.close()

if __name__ == "__main__":
    check_data() 