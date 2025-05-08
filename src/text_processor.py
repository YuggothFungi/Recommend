import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import re
from src.db import get_db_connection
import pymorphy2
from src.domain_phrases import DOMAIN_PHRASES, LEMMATIZATION_EXCEPTIONS

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
        
        # Инициализируем морфологический анализатор
        self.morph = pymorphy2.MorphAnalyzer()
        
        # Словарь тематических словосочетаний
        self.domain_phrases = DOMAIN_PHRASES
    
    def lemmatize_word(self, word):
        """Лемматизация одного слова с учетом части речи"""
        if '_' in word:  # Если это часть тематического словосочетания
            return word
            
        # Проверяем исключения
        if word in LEMMATIZATION_EXCEPTIONS:
            return LEMMATIZATION_EXCEPTIONS[word]
        
        # Получаем все варианты разбора
        parses = self.morph.parse(word)
        
        # Предпочитаем существительные
        for parse in parses:
            if 'NOUN' in parse.tag:
                return parse.normal_form
        
        # Если существительных нет, берем первый вариант
        return parses[0].normal_form
    
    def normalize_text(self, text):
        """Нормализация текста с сохранением тематических словосочетаний"""
        if not text:
            return ""
        
        print(f"\nОригинальный текст: {text}")
        
        # Приводим к нижнему регистру
        text = text.lower()
        print(f"После приведения к нижнему регистру: {text}")
        
        # Заменяем тематические словосочетания на их нормализованную форму
        for phrase, normalized in self.domain_phrases.items():
            if phrase in text:
                print(f"Найдено словосочетание: {phrase} -> {normalized}")
            text = text.replace(phrase, normalized.replace(' ', '_'))
        print(f"После замены словосочетаний: {text}")
        
        # Удаляем специальные символы и цифры, оставляем буквы, пробелы и подчеркивания
        text = re.sub(r'[^а-яёa-z\s_]', ' ', text)
        print(f"После удаления спецсимволов: {text}")
        
        # Токенизация
        tokens = word_tokenize(text, language='russian')
        print(f"После токенизации: {tokens}")
        
        # Проверяем составные термины
        i = 0
        while i < len(tokens) - 1:
            compound = f"{tokens[i]} {tokens[i+1]}"
            if compound.lower() in self.domain_phrases:
                tokens[i] = self.domain_phrases[compound.lower()].replace(' ', '_')
                tokens[i+1] = ''
            i += 1
        
        # Удаляем пустые токены
        tokens = [t for t in tokens if t]
        print(f"После обработки составных терминов: {tokens}")
        
        # Удаляем стоп-слова, сохраняя токены с подчеркиванием
        tokens = [token for token in tokens if token not in self.stop_words or '_' in token]
        print(f"После удаления стоп-слов: {tokens}")
        
        # Удаляем короткие слова (меньше 2 символов), сохраняя токены с подчеркиванием
        tokens = [token for token in tokens if len(token) > 2 or '_' in token]
        print(f"После удаления коротких слов: {tokens}")
        
        # Лемматизация каждого слова
        lemmatized_tokens = []
        for token in tokens:
            if '_' in token:
                print(f"Пропускаем лемматизацию для словосочетания: {token}")
                lemmatized_tokens.append(token)
            else:
                lemma = self.lemmatize_word(token)
                print(f"Лемматизация: {token} -> {lemma}")
                lemmatized_tokens.append(lemma)
        tokens = lemmatized_tokens
        print(f"После лемматизации: {tokens}")
        
        # Возвращаем подчеркивания на пробелы
        text = ' '.join(tokens).replace('_', ' ')
        print(f"Финальный результат: {text}\n")
        
        return text

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
    
    def process_disciplines(self, conn=None):
        """Обработка текстов дисциплин"""
        print("Обработка дисциплин...")
        if conn is None:
            conn = get_db_connection()
            should_close = True
        else:
            should_close = False
            
        cursor = conn.cursor()
        self._process_text(cursor, 'disciplines', 'id', ['name', 'goals', 'tasks'])
        conn.commit()
        
        if should_close:
            conn.close()
    
    def process_sections(self, conn=None):
        """Обработка текстов разделов"""
        print("Обработка разделов...")
        if conn is None:
            conn = get_db_connection()
            should_close = True
        else:
            should_close = False
            
        cursor = conn.cursor()
        self._process_text(cursor, 'sections', 'id', ['name', 'content'])
        conn.commit()
        
        if should_close:
            conn.close()
    
    def process_lecture_topics(self, conn=None):
        """Обработка текстов тем лекций"""
        print("Обработка тем лекций...")
        if conn is None:
            conn = get_db_connection()
            should_close = True
        else:
            should_close = False
            
        cursor = conn.cursor()
        self._process_text(cursor, 'lecture_topics', 'id', ['name'])
        conn.commit()
        
        if should_close:
            conn.close()
    
    def process_practical_topics(self, conn=None):
        """Обработка текстов тем практических занятий"""
        print("Обработка тем практических занятий...")
        if conn is None:
            conn = get_db_connection()
            should_close = True
        else:
            should_close = False
            
        cursor = conn.cursor()
        self._process_text(cursor, 'practical_topics', 'id', ['name'])
        conn.commit()
        
        if should_close:
            conn.close()
    
    def process_self_control_questions(self, conn=None):
        """Обработка текстов вопросов для самоконтроля"""
        print("Обработка вопросов для самоконтроля...")
        if conn is None:
            conn = get_db_connection()
            should_close = True
        else:
            should_close = False
            
        cursor = conn.cursor()
        self._process_text(cursor, 'self_control_questions', 'id', ['question'])
        conn.commit()
        
        if should_close:
            conn.close()
    
    def process_competencies(self, conn=None):
        """Обработка текстов компетенций"""
        print("Обработка компетенций...")
        if conn is None:
            conn = get_db_connection()
            should_close = True
        else:
            should_close = False
            
        cursor = conn.cursor()
        self._process_text(cursor, 'competencies', 'id', ['category', 'description'])
        conn.commit()
        
        if should_close:
            conn.close()
    
    def process_specialties(self, conn=None):
        """Обработка текстов специальностей"""
        print("Обработка специальностей...")
        if conn is None:
            conn = get_db_connection()
            should_close = True
        else:
            should_close = False
            
        cursor = conn.cursor()
        self._process_text(cursor, 'specialties', 'id', ['name'])
        conn.commit()
        
        if should_close:
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
    
    def process_all(self):
        """Обработка всех текстов"""
        conn = get_db_connection()
        try:
            self.process_disciplines(conn)
            self.process_sections(conn)
            self.process_lecture_topics(conn)
            self.process_practical_topics(conn)
            self.process_self_control_questions(conn)
            self.process_competencies(conn)
            self.process_specialties(conn)
            self.process_labor_functions(conn)
            self.process_labor_components(conn)
            print("Обработка текстов завершена!")
        finally:
            conn.close()

if __name__ == "__main__":
    processor = DatabaseTextProcessor()
    processor.process_all() 