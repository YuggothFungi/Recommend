import json
import os
import sys
import glob

# Добавляем корневую директорию в PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db import get_db_connection
from src.schema import init_db

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
    """Загрузка тем из JSON файлов в базу данных"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Очищаем таблицу тем
    cursor.execute('DELETE FROM topics')
    
    # Получаем все JSON файлы из директории
    json_files = glob.glob('input/curriculum_disciplines/*.json')
    
    for json_file in json_files:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # Определяем ключ для рабочей программы
            program_key = 'рабочая_программа' if 'рабочая_программа' in data else 'рабочая программа'
            
            # Получаем название дисциплины
            discipline_name = data['дисциплина']
            
            # Получаем ID дисциплины
            cursor.execute('SELECT id FROM disciplines WHERE name = ?', (discipline_name,))
            discipline_id = cursor.fetchone()[0]
            
            # Обрабатываем все семестры
            for semester in data[program_key]['семестры']:
                for section in semester['разделы']:
                    # Суммируем часы из лекций и практических занятий
                    total_hours = 0
                    if 'лекции' in section:
                        total_hours += sum(lecture['часы'] for lecture in section['лекции'])
                    if 'практические' in section:
                        total_hours += sum(practice['часы'] for practice in section['практические'])
                    
                    # Вставляем тему в базу данных
                    cursor.execute('''
                        INSERT INTO topics (discipline_id, title, description, hours)
                        VALUES (?, ?, ?, ?)
                    ''', (discipline_id, section['название'], section['содержание'], total_hours))
    
    conn.commit()
    conn.close()

def load_disciplines():
    """Загрузка дисциплин из файлов в директории curriculum_disciplines"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Очищаем таблицу перед загрузкой
    cursor.execute("DELETE FROM disciplines")
    
    # Получаем список всех JSON файлов в директории
    discipline_files = [f for f in os.listdir('input/curriculum_disciplines') 
                       if f.endswith('.json')]
    
    for file_name in discipline_files:
        with open(f'input/curriculum_disciplines/{file_name}', 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Получаем название дисциплины
        discipline_name = data['дисциплина']
        
        # Вставляем дисциплину в базу данных
        cursor.execute("""
            INSERT INTO disciplines (name) 
            VALUES (?)
        """, (discipline_name,))
    
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
    
    print("Загрузка дисциплин...")
    load_disciplines()
    
    print("Загрузка данных завершена!")

if __name__ == "__main__":
    load_all_data() 