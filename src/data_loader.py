import json
import os
from db import get_db_connection
from schema import init_db

def load_competencies():
    """Загрузка компетенций из abilities.json"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Очищаем таблицу перед загрузкой
    cursor.execute("DELETE FROM competencies")
    
    with open('input/abilities.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    for comp_id, comp_data in data.items():
        cursor.execute("""
            INSERT INTO competencies (id, category, description)
            VALUES (?, ?, ?)
        """, (comp_id, comp_data['категория'], comp_data['описание']))
    
    conn.commit()
    conn.close()

def load_labor_functions():
    """Загрузка трудовых функций из prof_std.json"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Очищаем таблицы перед загрузкой
    cursor.execute("DELETE FROM labor_function_components")
    cursor.execute("DELETE FROM labor_components")
    cursor.execute("DELETE FROM labor_functions")
    
    with open('input/prof_std.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    for func in data['профессиональный_стандарт']['трудовые_функции']:
        # Загружаем трудовую функцию
        cursor.execute("""
            INSERT INTO labor_functions (id, name)
            VALUES (?, ?)
        """, (func['идентификатор'], func['наименование']))
        
        # Загружаем трудовые действия
        for action in func['трудовые_действия']:
            cursor.execute("""
                INSERT INTO labor_components (component_type_id, description)
                VALUES (1, ?)
            """, (action,))
            
            # Получаем id созданного компонента
            cursor.execute("SELECT id FROM labor_components WHERE description = ?", (action,))
            component_id = cursor.fetchone()[0]
            
            # Создаем связь с трудовой функцией
            cursor.execute("""
                INSERT INTO labor_function_components (labor_function_id, component_id)
                VALUES (?, ?)
            """, (func['идентификатор'], component_id))
            
        # Загружаем необходимые умения
        for skill in func['необходимые_умения']:
            cursor.execute("""
                INSERT INTO labor_components (component_type_id, description)
                VALUES (2, ?)
            """, (skill,))
            
            cursor.execute("SELECT id FROM labor_components WHERE description = ?", (skill,))
            component_id = cursor.fetchone()[0]
            
            cursor.execute("""
                INSERT INTO labor_function_components (labor_function_id, component_id)
                VALUES (?, ?)
            """, (func['идентификатор'], component_id))
            
        # Загружаем необходимые знания
        for knowledge in func['необходимые_знания']:
            cursor.execute("""
                INSERT INTO labor_components (component_type_id, description)
                VALUES (3, ?)
            """, (knowledge,))
            
            cursor.execute("SELECT id FROM labor_components WHERE description = ?", (knowledge,))
            component_id = cursor.fetchone()[0]
            
            cursor.execute("""
                INSERT INTO labor_function_components (labor_function_id, component_id)
                VALUES (?, ?)
            """, (func['идентификатор'], component_id))
    
    conn.commit()
    conn.close()

def load_topics():
    """Загрузка тем из файлов в директории curriculum_disciplines"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Очищаем таблицы перед загрузкой
    cursor.execute("DELETE FROM topic_competency")
    cursor.execute("DELETE FROM topics")
    
    # Получаем список всех JSON файлов в директории
    discipline_files = [f for f in os.listdir('input/curriculum_disciplines') 
                       if f.endswith('.json')]
    
    for file_name in discipline_files:
        with open(f'input/curriculum_disciplines/{file_name}', 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Определяем ключ рабочей программы (может быть с пробелом или без)
        program_key = 'рабочая_программа' if 'рабочая_программа' in data else 'рабочая программа'
            
        # Загружаем темы из лекций и практических занятий
        for semester in data[program_key]['семестры']:
            for section in semester['разделы']:
                # Загружаем темы лекций
                for lecture in section['лекции']:
                    cursor.execute("""
                        INSERT INTO topics (title, description)
                        VALUES (?, ?)
                    """, (
                        lecture['тема'],
                        section['содержание']  # Используем содержание раздела как описание
                    ))
                    
                    topic_id = cursor.lastrowid
                    
                    # Создаем связи с компетенциями
                    for comp_id in data[program_key]['компетенции']:
                        cursor.execute("""
                            INSERT INTO topic_competency (topic_id, competency_id)
                            VALUES (?, ?)
                        """, (topic_id, comp_id))
                
                # Загружаем темы практических занятий
                for practice in section['практические']:
                    cursor.execute("""
                        INSERT INTO topics (title, description)
                        VALUES (?, ?)
                    """, (
                        practice['тема'],
                        section['содержание']  # Используем содержание раздела как описание
                    ))
                    
                    topic_id = cursor.lastrowid
                    
                    # Создаем связи с компетенциями
                    for comp_id in data[program_key]['компетенции']:
                        cursor.execute("""
                            INSERT INTO topic_competency (topic_id, competency_id)
                            VALUES (?, ?)
                        """, (topic_id, comp_id))
    
    conn.commit()
    conn.close()

def load_all_data():
    """Загрузка всех данных в базу данных"""
    print("Инициализация базы данных...")
    init_db()
    
    print("Загрузка компетенций...")
    load_competencies()
    
    print("Загрузка трудовых функций...")
    load_labor_functions()
    
    print("Загрузка тем...")
    load_topics()
    
    print("Загрузка данных завершена!")

if __name__ == "__main__":
    load_all_data() 