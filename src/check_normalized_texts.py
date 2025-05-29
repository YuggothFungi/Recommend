from src.db import get_db_connection
import logging

logger = logging.getLogger(__name__)

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
    
    # Проверяем дисциплины
    cursor.execute("""
        SELECT COUNT(*) 
        FROM disciplines 
        WHERE nltk_normalized_name IS NULL 
        OR nltk_normalized_goals IS NULL 
        OR nltk_normalized_tasks IS NULL
    """)
    unnormalized_disciplines = cursor.fetchone()[0]
    if unnormalized_disciplines > 0:
        raise ValueError(f"Есть {unnormalized_disciplines} ненормализованных текстов в таблице disciplines")
    
    # Проверяем разделы
    cursor.execute("""
        SELECT COUNT(*) 
        FROM sections 
        WHERE nltk_normalized_name IS NULL 
        OR nltk_normalized_content IS NULL
    """)
    unnormalized_sections = cursor.fetchone()[0]
    if unnormalized_sections > 0:
        raise ValueError(f"Есть {unnormalized_sections} ненормализованных текстов в таблице sections")
    
    # Проверяем темы лекций
    cursor.execute("""
        SELECT COUNT(*) 
        FROM lecture_topics 
        WHERE nltk_normalized_name IS NULL
    """)
    unnormalized_lectures = cursor.fetchone()[0]
    if unnormalized_lectures > 0:
        raise ValueError(f"Есть {unnormalized_lectures} ненормализованных текстов в таблице lecture_topics")
    
    # Проверяем темы практических занятий
    cursor.execute("""
        SELECT COUNT(*) 
        FROM practical_topics 
        WHERE nltk_normalized_name IS NULL
    """)
    unnormalized_practicals = cursor.fetchone()[0]
    if unnormalized_practicals > 0:
        raise ValueError(f"Есть {unnormalized_practicals} ненормализованных текстов в таблице practical_topics")
    
    # Проверяем вопросы для самоконтроля
    cursor.execute("""
        SELECT COUNT(*) 
        FROM self_control_questions 
        WHERE nltk_normalized_question IS NULL
    """)
    unnormalized_questions = cursor.fetchone()[0]
    if unnormalized_questions > 0:
        raise ValueError(f"Есть {unnormalized_questions} ненормализованных текстов в таблице self_control_questions")
    
    # Проверяем компетенции
    cursor.execute("""
        SELECT COUNT(*) 
        FROM competencies 
        WHERE nltk_normalized_category IS NULL 
        OR nltk_normalized_description IS NULL
    """)
    unnormalized_competencies = cursor.fetchone()[0]
    if unnormalized_competencies > 0:
        raise ValueError(f"Есть {unnormalized_competencies} ненормализованных текстов в таблице competencies")
    
    # Проверяем специальности
    cursor.execute("""
        SELECT COUNT(*) 
        FROM specialties 
        WHERE nltk_normalized_name IS NULL
    """)
    unnormalized_specialties = cursor.fetchone()[0]
    if unnormalized_specialties > 0:
        raise ValueError(f"Есть {unnormalized_specialties} ненормализованных текстов в таблице specialties")
    
    # Проверяем трудовые функции
    cursor.execute("""
        SELECT COUNT(*) 
        FROM labor_functions 
        WHERE nltk_normalized_name IS NULL
    """)
    unnormalized_functions = cursor.fetchone()[0]
    if unnormalized_functions > 0:
        raise ValueError(f"Есть {unnormalized_functions} ненормализованных текстов в таблице labor_functions")
    
    # Проверяем компоненты трудовых функций
    cursor.execute("""
        SELECT COUNT(*) 
        FROM labor_components 
        WHERE nltk_normalized_description IS NULL
    """)
    unnormalized_components = cursor.fetchone()[0]
    if unnormalized_components > 0:
        raise ValueError(f"Есть {unnormalized_components} ненормализованных текстов в таблице labor_components")
    
    print("Все тексты нормализованы")
    
    # Выводим примеры нормализованных текстов
    print("\nПримеры нормализованных текстов:")
    
    # Дисциплины
    print_normalized_texts(cursor, 'disciplines', 'name', 'nltk_normalized_name')
    print_normalized_texts(cursor, 'disciplines', 'goals', 'nltk_normalized_goals')
    print_normalized_texts(cursor, 'disciplines', 'tasks', 'nltk_normalized_tasks')
    
    # Разделы
    print_normalized_texts(cursor, 'sections', 'name', 'nltk_normalized_name')
    print_normalized_texts(cursor, 'sections', 'content', 'nltk_normalized_content')
    
    # Темы лекций
    print_normalized_texts(cursor, 'lecture_topics', 'name', 'nltk_normalized_name')
    
    # Темы практических занятий
    print_normalized_texts(cursor, 'practical_topics', 'name', 'nltk_normalized_name')
    
    # Вопросы для самоконтроля
    print_normalized_texts(cursor, 'self_control_questions', 'question', 'nltk_normalized_question')
    
    # Компетенции
    print_normalized_texts(cursor, 'competencies', 'category', 'nltk_normalized_category')
    print_normalized_texts(cursor, 'competencies', 'description', 'nltk_normalized_description')
    
    # Специальности
    print_normalized_texts(cursor, 'specialties', 'name', 'nltk_normalized_name')
    
    # Трудовые функции
    print_normalized_texts(cursor, 'labor_functions', 'name', 'nltk_normalized_name')
    
    # Компоненты трудовых функций
    print_normalized_texts(cursor, 'labor_components', 'description', 'nltk_normalized_description')

if __name__ == "__main__":
    conn = get_db_connection()
    check_normalized_texts(conn)
    conn.close() 