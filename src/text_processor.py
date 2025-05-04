import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import re
from src.db import get_db_connection

class TextProcessor:
    def __init__(self):
        # Загружаем необходимые ресурсы NLTK
        try:
            nltk.data.find('tokenizers/punkt')
            nltk.data.find('corpora/stopwords')
            nltk.data.find('tokenizers/punkt_tab')
        except LookupError as e:
            print(f"Ошибка: {e}")
            print("Пожалуйста, запустите src/download_nltk_data.py для загрузки необходимых ресурсов")
            raise
        
        # Загружаем стоп-слова
        self.stop_words = set(stopwords.words('russian'))
        # Добавляем дополнительные стоп-слова
        self.stop_words.update(['это', 'который', 'которые', 'которых', 'которым', 'которыми'])
    
    def normalize_text(self, text):
        """Нормализация текста"""
        if not text:
            return ""
        
        # Приводим к нижнему регистру
        text = text.lower()
        
        # Удаляем специальные символы и цифры, оставляем буквы и пробелы
        text = re.sub(r'[^а-яёa-z\s]', ' ', text)
        
        # Токенизация
        tokens = word_tokenize(text, language='russian')
        
        # Удаляем стоп-слова
        tokens = [token for token in tokens if token not in self.stop_words]
        
        # Удаляем короткие слова (меньше 2 символов)
        tokens = [token for token in tokens if len(token) > 2]
        
        # Объединяем токены обратно в текст
        return ' '.join(tokens)

class DatabaseTextProcessor:
    def __init__(self):
        self.text_processor = TextProcessor()
    
    def _process_text(self, cursor, table_name, id_field, text_fields):
        """Обработка текстов в указанной таблице"""
        # Формируем SQL-запрос для получения текстов
        select_fields = ', '.join([f't.{field}' for field in text_fields])
        cursor.execute(f"""
            SELECT t.{id_field}, {select_fields}
            FROM {table_name} t
        """)
        
        # Обрабатываем каждый текст
        for row in cursor.fetchall():
            id_value = row[0]
            updates = {}
            
            # Обрабатываем каждое текстовое поле
            for i, field in enumerate(text_fields, 1):
                original_text = row[i]
                if original_text:
                    normalized_text = self.text_processor.normalize_text(original_text)
                    updates[f'nltk_normalized_{field}'] = normalized_text
            
            # Обновляем записи в базе
            if updates:
                # Проверяем существование колонок
                for column in updates.keys():
                    cursor.execute(f"""
                        SELECT COUNT(*) 
                        FROM pragma_table_info('{table_name}') 
                        WHERE name = ?
                    """, (column,))
                    if cursor.fetchone()[0] == 0:
                        cursor.execute(f"""
                            ALTER TABLE {table_name}
                            ADD COLUMN {column} TEXT
                        """)
                
                # Обновляем значения
                set_clause = ', '.join([f'{k} = ?' for k in updates.keys()])
                values = list(updates.values()) + [id_value]
                cursor.execute(f"""
                    UPDATE {table_name}
                    SET {set_clause}
                    WHERE {id_field} = ?
                """, values)
    
    def process_competencies(self):
        """Обработка текстов компетенций"""
        print("Обработка компетенций...")
        conn = get_db_connection()
        cursor = conn.cursor()
        
        self._process_text(cursor, 'competencies', 'id', ['category', 'description'])
        
        conn.commit()
        conn.close()
    
    def process_labor_functions(self, conn=None):
        """Обработка текстов трудовых функций"""
        print("Обработка трудовых функций...")
        if conn is None:
            conn = get_db_connection()
            should_close = True
        else:
            should_close = False
            
        cursor = conn.cursor()
        self._process_text(cursor, 'labor_functions', 'id', ['name'])
        conn.commit()
        
        if should_close:
            conn.close()
    
    def process_labor_components(self, conn=None):
        """Обработка текстов компонентов трудовых функций"""
        print("Обработка компонентов трудовых функций...")
        if conn is None:
            conn = get_db_connection()
            should_close = True
        else:
            should_close = False
            
        cursor = conn.cursor()
        self._process_text(cursor, 'labor_components', 'id', ['description'])
        conn.commit()
        
        if should_close:
            conn.close()
    
    def process_topics(self, conn=None):
        """Обработка текстов тем"""
        print("Обработка тем...")
        if conn is None:
            conn = get_db_connection()
            should_close = True
        else:
            should_close = False
            
        cursor = conn.cursor()
        self._process_text(cursor, 'topics', 'id', ['title', 'description'])
        conn.commit()
        
        if should_close:
            conn.close()
    
    def process_all(self):
        """Обработка всех текстов"""
        self.process_competencies()
        self.process_labor_functions()
        self.process_labor_components()
        self.process_topics()
        print("Обработка текстов завершена!")

if __name__ == "__main__":
    processor = DatabaseTextProcessor()
    processor.process_all() 