import nltk
from nltk.corpus import stopwords
import pymorphy2
import re
from db import get_db_connection

class TextProcessor:
    def __init__(self):
        # Инициализация pymorphy2
        self.morph = pymorphy2.MorphAnalyzer()
        
        # Загрузка стоп-слов
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('stopwords')
        
        self.stop_words = set(stopwords.words('russian'))
        # Добавляем дополнительные стоп-слова
        self.stop_words.update(['это', 'который', 'который', 'который', 'который', 'который'])
        
        # Регулярное выражение для удаления специальных символов
        self.pattern = re.compile(r'[^\w\s]')
    
    def normalize_text(self, text):
        """Нормализация текста: удаление спецсимволов, стоп-слов и лемматизация"""
        if not text:
            return ""
            
        # Приводим к нижнему регистру
        text = text.lower()
        
        # Удаляем специальные символы
        text = self.pattern.sub(' ', text)
        
        # Разбиваем на слова
        words = text.split()
        
        # Удаляем стоп-слова и лемматизируем
        normalized_words = []
        for word in words:
            if word not in self.stop_words:
                parsed = self.morph.parse(word)[0]
                normalized_words.append(parsed.normal_form)
        
        return ' '.join(normalized_words)

class DatabaseTextProcessor:
    def __init__(self):
        self.text_processor = TextProcessor()
    
    def process_topics(self):
        """Обработка текстов тем"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Получаем все темы
        cursor.execute("SELECT id, title, description FROM topics")
        topics = cursor.fetchall()
        
        for topic in topics:
            topic_id, title, description = topic
            
            # Нормализуем заголовок и описание
            normalized_title = self.text_processor.normalize_text(title)
            normalized_description = self.text_processor.normalize_text(description)
            
            # Обновляем запись
            cursor.execute("""
                UPDATE topics 
                SET pymorphy2_nltk_normalized_title = ?, 
                    pymorphy2_nltk_normalized_description = ?
                WHERE id = ?
            """, (normalized_title, normalized_description, topic_id))
        
        conn.commit()
        conn.close()
    
    def process_competencies(self):
        """Обработка текстов компетенций"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Получаем все компетенции
        cursor.execute("SELECT id, category, description FROM competencies")
        competencies = cursor.fetchall()
        
        for comp in competencies:
            comp_id, category, description = comp
            
            # Нормализуем категорию и описание
            normalized_category = self.text_processor.normalize_text(category)
            normalized_description = self.text_processor.normalize_text(description)
            
            # Обновляем запись
            cursor.execute("""
                UPDATE competencies 
                SET pymorphy2_nltk_normalized_category = ?, 
                    pymorphy2_nltk_normalized_description = ?
                WHERE id = ?
            """, (normalized_category, normalized_description, comp_id))
        
        conn.commit()
        conn.close()
    
    def process_labor_functions(self):
        """Обработка текстов трудовых функций"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Получаем все трудовые функции
        cursor.execute("SELECT id, name FROM labor_functions")
        functions = cursor.fetchall()
        
        for func in functions:
            func_id, name = func
            
            # Нормализуем название
            normalized_name = self.text_processor.normalize_text(name)
            
            # Обновляем запись
            cursor.execute("""
                UPDATE labor_functions 
                SET pymorphy2_nltk_normalized_name = ?
                WHERE id = ?
            """, (normalized_name, func_id))
        
        conn.commit()
        conn.close()
    
    def process_labor_components(self):
        """Обработка текстов компонентов трудовых функций"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Получаем все компоненты
        cursor.execute("SELECT id, description FROM labor_components")
        components = cursor.fetchall()
        
        for comp in components:
            comp_id, description = comp
            
            # Нормализуем описание
            normalized_description = self.text_processor.normalize_text(description)
            
            # Обновляем запись
            cursor.execute("""
                UPDATE labor_components 
                SET pymorphy2_nltk_normalized_description = ?
                WHERE id = ?
            """, (normalized_description, comp_id))
        
        conn.commit()
        conn.close()
    
    def process_all(self):
        """Обработка всех текстов в базе данных"""
        print("Обработка тем...")
        self.process_topics()
        
        print("Обработка компетенций...")
        self.process_competencies()
        
        print("Обработка трудовых функций...")
        self.process_labor_functions()
        
        print("Обработка компонентов трудовых функций...")
        self.process_labor_components()
        
        print("Обработка текстов завершена!")

if __name__ == "__main__":
    processor = DatabaseTextProcessor()
    processor.process_all() 