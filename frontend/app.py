import os
import sys
import traceback
import logging

# Добавляем корневую директорию в PYTHONPATH
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)

from flask import Flask, render_template, jsonify, request
from src.db import get_db_connection

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/disciplines')
def get_disciplines():
    try:
        logger.debug("Получение списка дисциплин")
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, name FROM disciplines')
        disciplines = [{'id': row['id'], 'name': row['name']} for row in cursor.fetchall()]
        conn.close()
        logger.debug(f"Найдено дисциплин: {len(disciplines)}")
        return jsonify(disciplines)
    except Exception as e:
        logger.error(f"Ошибка при получении дисциплин: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/topics')
def get_topics():
    try:
        discipline_id = request.args.get('discipline_id')
        logger.debug(f"Получение тем для дисциплины {discipline_id}")
        
        if not discipline_id:
            logger.warning("Не указан ID дисциплины")
            return jsonify({'error': 'Discipline ID is required'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Проверяем существование дисциплины
        cursor.execute('SELECT id FROM disciplines WHERE id = ?', (discipline_id,))
        if not cursor.fetchone():
            logger.warning(f"Дисциплина с ID {discipline_id} не найдена")
            return jsonify({'error': 'Discipline not found'}), 404
        
        # Получаем лекционные темы через разделы
        cursor.execute('''
            SELECT lt.id, lt.name, lt.hours, 'lecture' as type 
            FROM lecture_topics lt
            JOIN sections s ON lt.section_id = s.id
            WHERE s.discipline_id = ?
        ''', (discipline_id,))
        lecture_topics = []
        for row in cursor.fetchall():
            topic = {
                'id': row['id'],
                'name': row['name'],
                'hours': row['hours'],
                'type': row['type']
            }
            lecture_topics.append(topic)
        logger.debug(f"Найдено лекционных тем: {len(lecture_topics)}")
        
        # Получаем практические темы через разделы
        cursor.execute('''
            SELECT pt.id, pt.name, pt.hours, 'practical' as type 
            FROM practical_topics pt
            JOIN sections s ON pt.section_id = s.id
            WHERE s.discipline_id = ?
        ''', (discipline_id,))
        practical_topics = []
        for row in cursor.fetchall():
            topic = {
                'id': row['id'],
                'name': row['name'],
                'hours': row['hours'],
                'type': row['type']
            }
            practical_topics.append(topic)
        logger.debug(f"Найдено практических тем: {len(practical_topics)}")
        
        # Объединяем темы
        topics = lecture_topics + practical_topics
        logger.debug(f"Всего тем: {len(topics)}")
        
        conn.close()
        return jsonify(topics)
    except Exception as e:
        logger.error(f"Ошибка при получении тем: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/labor-functions')
def get_labor_functions():
    try:
        logger.debug("Получение всех трудовых функций")
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, name FROM labor_functions ORDER BY name')
        functions = [{'id': row['id'], 'name': row['name']} for row in cursor.fetchall()]
        conn.close()
        logger.debug(f"Найдено трудовых функций: {len(functions)}")
        return jsonify(functions)
    except Exception as e:
        logger.error(f"Ошибка при получении трудовых функций: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/similarities')
def get_similarities():
    try:
        topic_id = request.args.get('topic_id')
        similarity_type = request.args.get('similarity_type', 'rubert')
        logger.debug(f"Получение сходства для темы {topic_id}, тип: {similarity_type}")
        
        if not topic_id:
            logger.warning("Не указан ID темы")
            return jsonify({'error': 'Topic ID is required'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Получаем сходства
        cursor.execute('''
            SELECT lf.id, lf.name, sr.similarity_score
            FROM labor_functions lf
            LEFT JOIN similarity_results sr ON sr.labor_function_id = lf.id 
            AND sr.topic_id = ? AND sr.similarity_type = ?
            WHERE lf.discipline_id = (
                SELECT discipline_id FROM (
                    SELECT discipline_id FROM lecture_topics WHERE id = ?
                    UNION
                    SELECT discipline_id FROM practical_topics WHERE id = ?
                )
            )
        ''', (topic_id, similarity_type, topic_id, topic_id))
        
        similarities = [{'id': row['id'], 'name': row['name'], 'similarity': row['similarity_score']} for row in cursor.fetchall()]
        logger.debug(f"Найдено сходств: {len(similarities)}")
        
        # Получаем рекомендации
        recommendations = []
        if similarities:
            avg_similarity = sum(s['similarity'] for s in similarities if s['similarity'] is not None) / len(similarities)
            logger.debug(f"Среднее сходство: {avg_similarity}")
            
            if avg_similarity < 0.3:
                recommendations.append("Тема не обеспечивает трудовые функции")
            elif avg_similarity < 0.5:
                recommendations.append("Рекомендуется уделить больше времени для изучения темы")
            elif avg_similarity < 0.7:
                recommendations.append("Возможно требуется перефразирование темы для лучшего текстового сходства")
            else:
                recommendations.append("Тема хорошо удовлетворяет трудовым функциям")
        else:
            recommendations.append("Для выбранной трудовой функции нет подходящих тем")
        
        conn.close()
        return jsonify({
            "similarities": similarities,
            "recommendations": recommendations
        })
    except Exception as e:
        logger.error(f"Ошибка при получении сходства: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 