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
        labor_function_id = request.args.get('labor_function_id')
        similarity_type = request.args.get('similarity_type', 'rubert')
        threshold = float(request.args.get('threshold', 0.0))
        configuration_id = request.args.get('configuration_id')
        logger.debug(f"Получение сходства: topic_id={topic_id}, labor_function_id={labor_function_id}, тип={similarity_type}, порог={threshold}, конфигурация={configuration_id}")
        
        if not configuration_id:
            logger.warning("Не указан ID конфигурации")
            return jsonify({'error': 'Configuration ID is required'}), 400
        if not (topic_id or labor_function_id):
            logger.warning("Не указан ни topic_id, ни labor_function_id")
            return jsonify({'error': 'Topic ID or Labor Function ID is required'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        similarity_field = f"{similarity_type}_similarity"
        result = []
        if topic_id:
            # Отбор функций по теме
            cursor.execute(f'''
                SELECT lf.id, lf.name, MAX(sr.{similarity_field}) as similarity
                FROM similarity_results sr
                JOIN labor_functions lf ON lf.id = sr.labor_function_id
                WHERE sr.topic_id = ?
                  AND sr.configuration_id = ?
                  AND sr.{similarity_field} > ?
                GROUP BY lf.id, lf.name
                ORDER BY similarity DESC
            ''', (topic_id, configuration_id, threshold))
            for row in cursor.fetchall():
                result.append({
                    'id': row['id'],
                    'name': row['name'],
                    'similarity': row['similarity']
                })
            logger.debug(f"Найдено уникальных функций с подходящим сходством: {len(result)}")
            conn.close()
            return jsonify({'functions': result})
        else:
            # Отбор тем по трудовой функции
            cursor.execute(f'''
                SELECT sr.topic_id, sr.topic_type, COALESCE(lt.name, pt.name) as name, 
                       COALESCE(lt.hours, pt.hours) as hours, MAX(sr.{similarity_field}) as similarity
                FROM similarity_results sr
                LEFT JOIN lecture_topics lt ON sr.topic_type = 'lecture' AND sr.topic_id = lt.id
                LEFT JOIN practical_topics pt ON sr.topic_type = 'practical' AND sr.topic_id = pt.id
                WHERE sr.labor_function_id = ?
                  AND sr.configuration_id = ?
                  AND sr.{similarity_field} > ?
                GROUP BY sr.topic_id, sr.topic_type, COALESCE(lt.name, pt.name), COALESCE(lt.hours, pt.hours)
                ORDER BY similarity DESC
            ''', (labor_function_id, configuration_id, threshold))
            for row in cursor.fetchall():
                result.append({
                    'id': row['topic_id'],
                    'name': row['name'],
                    'type': row['topic_type'],
                    'hours': row['hours'],
                    'similarity': row['similarity']
                })
            logger.debug(f"Найдено уникальных тем с подходящим сходством: {len(result)}")
            conn.close()
            return jsonify({'topics': result})
    except Exception as e:
        logger.error(f"Ошибка при получении сходства: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/configurations')
def get_configurations():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, description FROM vectorization_configurations ORDER BY id')
        configs = []
        for row in cursor.fetchall():
            configs.append({
                'id': row['id'],
                'name': row['name'],
                'description': row['description']
            })
        conn.close()
        return jsonify(configs)
    except Exception as e:
        logger.error(f"Ошибка при получении конфигураций: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 