import json
import os
import sys
import glob

# Добавляем корневую директорию в PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db import get_db_connection
from src.schema import init_db, reset_db

def load_competencies():
    """Загрузка компетенций из JSON файла"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Очищаем таблицу перед загрузкой
    cursor.execute("DELETE FROM competencies")
    
    with open('input/competencies.json', 'r', encoding='utf-8') as f:
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
    cursor.execute("DELETE FROM labor_components")
    cursor.execute("DELETE FROM specialty_labor_functions")
    cursor.execute("DELETE FROM labor_functions")
    cursor.execute("DELETE FROM specialties")
    
    with open('input/prof_std.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    # Загружаем специальность
    specialty_name = data['профессиональный_стандарт']['специальность']
    cursor.execute("""
        INSERT INTO specialties (name)
        VALUES (?)
    """, (specialty_name,))
    specialty_id = cursor.lastrowid
        
    for func in data['профессиональный_стандарт']['трудовые_функции']:
        # Загружаем трудовую функцию
        cursor.execute("""
            INSERT INTO labor_functions (id, code, name, qualification_level)
            VALUES (?, ?, ?, ?)
        """, (func['идентификатор'], func['код'], func['наименование'], func['уровень_квалификации']))
        
        # Создаем связь с специальностью
        cursor.execute("""
            INSERT INTO specialty_labor_functions (specialty_id, labor_function_id)
            VALUES (?, ?)
        """, (specialty_id, func['идентификатор']))
        
        # Загружаем трудовые действия
        for action in func['трудовые_действия']:
            cursor.execute("""
                INSERT INTO labor_components (labor_function_id, component_type_id, description)
                VALUES (?, 1, ?)
            """, (func['идентификатор'], action))
            
        # Загружаем необходимые умения
        for skill in func['необходимые_умения']:
            cursor.execute("""
                INSERT INTO labor_components (labor_function_id, component_type_id, description)
                VALUES (?, 2, ?)
            """, (func['идентификатор'], skill))
            
        # Загружаем необходимые знания
        for knowledge in func['необходимые_знания']:
            cursor.execute("""
                INSERT INTO labor_components (labor_function_id, component_type_id, description)
                VALUES (?, 3, ?)
            """, (func['идентификатор'], knowledge))
            
        # Загружаем другие характеристики
        if 'другие_характеристики' in func:
            for other in func['другие_характеристики']:
                cursor.execute("""
                    INSERT INTO labor_components (labor_function_id, component_type_id, description)
                    VALUES (?, 4, ?)
                """, (func['идентификатор'], other))
    
    conn.commit()
    conn.close()

def load_curriculum_discipline(data, cursor):
    """Загрузка данных одной учебной дисциплины"""
    # Определяем ключ для рабочей программы
    program_key = 'рабочая_программа' if 'рабочая_программа' in data else 'рабочая программа'
    
    # Получаем название дисциплины
    discipline_name = data['дисциплина']
    
    # Преобразуем списки целей и задач в строки
    goals = '\n'.join(data[program_key].get('цели', [])) if isinstance(data[program_key].get('цели'), list) else data[program_key].get('цели', '')
    tasks = '\n'.join(data[program_key].get('задачи', [])) if isinstance(data[program_key].get('задачи'), list) else data[program_key].get('задачи', '')
    
    # Вставляем дисциплину
    cursor.execute("""
        INSERT INTO disciplines (name, goals, tasks)
        VALUES (?, ?, ?)
    """, (discipline_name, goals, tasks))
    discipline_id = cursor.lastrowid
    
    # Добавляем компетенции
    if 'компетенции' in data[program_key]:
        for comp_id in data[program_key]['компетенции']:
            cursor.execute("""
                INSERT INTO discipline_competencies (discipline_id, competency_id)
                VALUES (?, ?)
            """, (discipline_id, comp_id))
    
    # Обрабатываем семестры
    for semester_data in data[program_key]['семестры']:
        # Получаем id семестра (семестры уже предзаполнены)
        cursor.execute("SELECT id FROM semesters WHERE number = ?", (semester_data['номер'],))
        semester_id = cursor.fetchone()[0]
        
        # Связываем семестр с дисциплиной
        cursor.execute("""
            INSERT INTO discipline_semesters (discipline_id, semester_id)
            VALUES (?, ?)
        """, (discipline_id, semester_id))
        
        # Обрабатываем разделы
        for section_data in semester_data['разделы']:
            # Добавляем раздел
            cursor.execute("""
                INSERT INTO sections (discipline_id, semester_id, number, name, content)
                VALUES (?, ?, ?, ?, ?)
            """, (
                discipline_id,
                semester_id,
                section_data['номер'],
                section_data['название'],
                section_data['содержание']
            ))
            section_id = cursor.lastrowid
            
            # Добавляем темы лекций
            if 'лекции' in section_data:
                for lecture in section_data['лекции']:
                    cursor.execute("""
                        INSERT INTO lecture_topics (section_id, name, hours)
                        VALUES (?, ?, ?)
                    """, (section_id, lecture['тема'], lecture['часы']))
            
            # Добавляем темы практических занятий
            if 'практические' in section_data:
                for practice in section_data['практические']:
                    cursor.execute("""
                        INSERT INTO practical_topics (section_id, name, hours)
                        VALUES (?, ?, ?)
                    """, (section_id, practice['тема'], practice['часы']))
            
            # Добавляем вопросы для самоконтроля
            if 'вопросы' in section_data:
                for question in section_data['вопросы']:
                    cursor.execute("""
                        INSERT INTO self_control_questions (section_id, question)
                        VALUES (?, ?)
                    """, (section_id, question))

def load_curriculum():
    """Загрузка учебных планов из JSON файлов"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Очищаем таблицы перед загрузкой
    cursor.execute("DELETE FROM self_control_questions")
    cursor.execute("DELETE FROM lecture_topics")
    cursor.execute("DELETE FROM practical_topics")
    cursor.execute("DELETE FROM sections")
    cursor.execute("DELETE FROM discipline_semesters")
    cursor.execute("DELETE FROM discipline_competencies")
    # Не очищаем таблицу semesters, так как она предзаполнена
    cursor.execute("DELETE FROM disciplines")
    
    # Получаем все JSON файлы из директории
    json_files = glob.glob('input/curriculum_disciplines/*.json')
    
    for json_file in json_files:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            load_curriculum_discipline(data, cursor)
    
    conn.commit()
    conn.close()

def load_all_data():
    """Загрузка всех данных в базу данных"""
    print("Сброс базы данных...")
    reset_db()
    
    print("Инициализация базы данных...")
    init_db()
    
    print("Загрузка компетенций...")
    load_competencies()
    
    print("Загрузка трудовых функций...")
    load_labor_functions()
    
    print("Загрузка учебных планов...")
    load_curriculum()
    
    print("Загрузка данных завершена!")

if __name__ == "__main__":
    load_all_data() 