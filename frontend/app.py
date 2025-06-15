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
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
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
        topic_type = request.args.get('topic_type')
        labor_function_id = request.args.get('labor_function_id')
        similarity_type = request.args.get('similarity_type', 'rubert')
        threshold = float(request.args.get('threshold', 0.0))
        configuration_id = request.args.get('configuration_id')
        logger.debug(f"Получение сходства: topic_id={topic_id}, topic_type={topic_type}, labor_function_id={labor_function_id}, тип={similarity_type}, порог={threshold}, конфигурация={configuration_id}")
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
            if not topic_type:
                logger.warning("Не указан topic_type при переданном topic_id")
                return jsonify({'error': 'Topic type is required when topic_id is provided'}), 400
            # Отбор функций по теме
            cursor.execute(f'''
                SELECT lf.id, lf.name, MAX(sr.{similarity_field}) as similarity
                FROM similarity_results sr
                JOIN labor_functions lf ON lf.id = sr.labor_function_id
                WHERE sr.topic_id = ?
                  AND sr.topic_type = ?
                  AND sr.configuration_id = ?
                  AND sr.{similarity_field} > ?
                GROUP BY lf.id, lf.name
                ORDER BY similarity DESC
            ''', (topic_id, topic_type, configuration_id, threshold))
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

def analyze_similarity_comparison(comparison, threshold=0.3):
    """
    Анализирует сравнение сходства и формирует рекомендации.
    
    Args:
        comparison (list): Список сравнений сходства
        threshold (float): Порог разницы для формирования рекомендации
        
    Returns:
        list: Список рекомендаций
    """
    logger.debug(f"Анализ сравнения сходства. Количество сравнений: {len(comparison)}")
    recommendations = []
    
    for comp in comparison:
        logger.debug(f"Анализ сравнения: TF-IDF={comp['tfidf_score']:.2f}, ruBERT={comp['rubert_score']:.2f}")
        
        # Если ruBERT показывает высокое сходство, а TF-IDF низкое
        if comp['rubert_score'] > 0.7 and comp['tfidf_score'] < 0.2:
            logger.debug(f"Обнаружено расхождение: ruBERT высокое, TF-IDF низкое")
            recommendations.append({
                'type': 'warning',
                'message': f"Для трудовой функции '{comp['function_name']}' обнаружено расхождение в оценках сходства: "
                          f"ruBERT ({comp['rubert_score']:.2f}) показывает высокое сходство, "
                          f"а TF-IDF ({comp['tfidf_score']:.2f}) - низкое. "
                          f"Рекомендуется уточнить формулировку темы для лучшего соответствия."
            })
        # Если TF-IDF показывает высокое сходство, а ruBERT низкое
        elif comp['tfidf_score'] > 0.7 and comp['rubert_score'] < 0.2:
            logger.debug(f"Обнаружено расхождение: TF-IDF высокое, ruBERT низкое")
            recommendations.append({
                'type': 'warning',
                'message': f"Для трудовой функции '{comp['function_name']}' обнаружено расхождение в оценках сходства: "
                          f"TF-IDF ({comp['tfidf_score']:.2f}) показывает высокое сходство, "
                          f"а ruBERT ({comp['rubert_score']:.2f}) - низкое. "
                          f"Рекомендуется переформулировать тему с использованием более точных терминов."
            })
        # # Если разница между оценками значительная
        # elif comp['difference'] > threshold:
        #     logger.debug(f"Обнаружена значительная разница: {comp['difference']:.2f}")
        #     recommendations.append({
        #         'type': 'info',
        #         'message': f"Для трудовой функции '{comp['function_name']}' обнаружена значительная разница "
        #                   f"между оценками сходства: TF-IDF ({comp['tfidf_score']:.2f}), "
        #                   f"ruBERT ({comp['rubert_score']:.2f}). "
        #                   f"Рекомендуется проверить соответствие формулировок."
        #     })
    
    logger.debug(f"Сформировано рекомендаций: {len(recommendations)}")
    return recommendations

@app.route('/api/similarity-comparison')
def get_similarity_comparison():
    topic_id = request.args.get('topic_id')
    configuration_id = request.args.get('configuration_id')
    
    if not topic_id:
        return jsonify({'error': 'Не указан ID темы'}), 400
    if not configuration_id:
        return jsonify({'error': 'Не указан ID конфигурации'}), 400
        
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Получаем сходство для TF-IDF
        cursor.execute('''
            SELECT lf.id, lf.name, MAX(sr.tfidf_similarity) as score
            FROM similarity_results sr
            JOIN labor_functions lf ON lf.id = sr.labor_function_id
            WHERE sr.topic_id = ?
              AND sr.configuration_id = ?
            GROUP BY lf.id, lf.name
        ''', (topic_id, configuration_id))
        tfidf_similarities = []
        for row in cursor.fetchall():
            tfidf_similarities.append({
                'function_id': row['id'],
                'function_name': row['name'],
                'score': row['score']
            })
            
        # Получаем сходство для ruBERT
        cursor.execute('''
            SELECT lf.id, lf.name, MAX(sr.rubert_similarity) as score
            FROM similarity_results sr
            JOIN labor_functions lf ON lf.id = sr.labor_function_id
            WHERE sr.topic_id = ?
              AND sr.configuration_id = ?
            GROUP BY lf.id, lf.name
        ''', (topic_id, configuration_id))
        rubert_similarities = []
        for row in cursor.fetchall():
            rubert_similarities.append({
                'function_id': row['id'],
                'function_name': row['name'],
                'score': row['score']
            })
        
        # Формируем сравнение
        comparison = []
        for tfidf_sim in tfidf_similarities:
            rubert_sim = next(
                (s for s in rubert_similarities if s['function_id'] == tfidf_sim['function_id']),
                None
            )
            
            if rubert_sim:
                comparison.append({
                    'function_id': tfidf_sim['function_id'],
                    'function_name': tfidf_sim['function_name'],
                    'tfidf_score': tfidf_sim['score'],
                    'rubert_score': rubert_sim['score'],
                    'difference': abs(tfidf_sim['score'] - rubert_sim['score'])
                })
        
        # Анализируем сравнение и формируем рекомендации
        recommendations = analyze_similarity_comparison(comparison)
        
        conn.close()
        return jsonify({
            'comparison': comparison,
            'recommendations': recommendations
        })
        
    except Exception as e:
        logger.error(f"Ошибка при получении сравнения сходства: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/keywords')
def get_keywords():
    try:
        entity_id = request.args.get('entity_id')
        entity_type = request.args.get('entity_type')
        config_id = request.args.get('config_id')
        
        if not all([entity_id, entity_type, config_id]):
            return jsonify({'error': 'Missing required parameters'}), 400
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Получаем название сущности в зависимости от типа
        if entity_type == 'lecture_topic':
            cursor.execute('SELECT name FROM lecture_topics WHERE id = ?', (entity_id,))
        elif entity_type == 'practical_topic':
            cursor.execute('SELECT name FROM practical_topics WHERE id = ?', (entity_id,))
        else:  # labor_function
            cursor.execute('SELECT name FROM labor_functions WHERE id = ?', (entity_id,))
            
        entity = cursor.fetchone()
        if not entity:
            return jsonify({'error': 'Entity not found'}), 404
            
        # Получаем ключевые слова
        cursor.execute('''
            SELECT keyword, weight
            FROM keywords
            WHERE entity_id = ? 
              AND entity_type = ?
              AND configuration_id = ?
            ORDER BY weight DESC
            LIMIT 5
        ''', (entity_id, entity_type, config_id))
        
        keywords = [{'keyword': row['keyword'], 'weight': row['weight']} 
                   for row in cursor.fetchall()]
        
        conn.close()
        return jsonify({
            'name': entity['name'],
            'keywords': keywords
        })
    except Exception as e:
        logger.error(f"Ошибка при получении ключевых слов: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/isolated-elements')
def get_isolated_elements():
    try:
        threshold = float(request.args.get('threshold', 0.3))
        similarity_type = request.args.get('similarity_type', 'rubert')
        config_id = request.args.get('configuration_id')
        discipline_id = request.args.get('discipline_id')
        
        if not config_id:
            return jsonify({'error': 'Configuration ID is required'}), 400
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Определяем поле сходства в зависимости от типа
        similarity_field = f"{similarity_type}_similarity"
        
        # Получаем изолированные темы
        topics_query = f'''
            SELECT 
                sr.topic_id,
                sr.topic_type,
                CASE 
                    WHEN sr.topic_type = 'lecture' THEN lt.name
                    ELSE pt.name
                END as name,
                MAX(sr.{similarity_field}) as max_similarity
            FROM similarity_results sr
            LEFT JOIN lecture_topics lt ON sr.topic_type = 'lecture' AND sr.topic_id = lt.id
            LEFT JOIN practical_topics pt ON sr.topic_type = 'practical' AND sr.topic_id = pt.id
            LEFT JOIN sections s ON (sr.topic_type = 'lecture' AND lt.section_id = s.id) 
                OR (sr.topic_type = 'practical' AND pt.section_id = s.id)
            WHERE sr.configuration_id = ?
        '''
        
        topics_params = [config_id]
        
        if discipline_id:
            topics_query += ' AND s.discipline_id = ?'
            topics_params.append(discipline_id)
            
        topics_query += '''
            GROUP BY sr.topic_id, sr.topic_type
            HAVING max_similarity < ? OR max_similarity IS NULL
            ORDER BY max_similarity ASC
        '''
        topics_params.append(threshold)
        
        cursor.execute(topics_query, topics_params)
        
        isolated_topics = []
        for row in cursor.fetchall():
            isolated_topics.append({
                'id': row['topic_id'],
                'name': row['name'],
                'type': row['topic_type'],
                'max_similarity': row['max_similarity']
            })
            
        # Получаем изолированные трудовые функции
        functions_query = '''
            SELECT 
                lf.id,
                lf.name,
                MAX(sr.{similarity_field}) as max_similarity
            FROM labor_functions lf
            LEFT JOIN similarity_results sr ON lf.id = sr.labor_function_id 
                AND sr.configuration_id = ?
        '''
        
        functions_params = [config_id]
        
        if discipline_id:
            functions_query += '''
                LEFT JOIN lecture_topics lt ON sr.topic_type = 'lecture' AND sr.topic_id = lt.id
                LEFT JOIN practical_topics pt ON sr.topic_type = 'practical' AND sr.topic_id = pt.id
                LEFT JOIN sections s ON (sr.topic_type = 'lecture' AND lt.section_id = s.id) 
                    OR (sr.topic_type = 'practical' AND pt.section_id = s.id)
                WHERE s.discipline_id = ?
            '''
            functions_params.append(discipline_id)
            
        functions_query += '''
            GROUP BY lf.id, lf.name
            HAVING max_similarity < ? OR max_similarity IS NULL
            ORDER BY max_similarity ASC
        '''
        functions_params.append(threshold)
        
        cursor.execute(functions_query.format(similarity_field=similarity_field), functions_params)
        
        isolated_functions = []
        for row in cursor.fetchall():
            isolated_functions.append({
                'id': row['id'],
                'name': row['name'],
                'max_similarity': row['max_similarity']
            })
            
        conn.close()
        
        return jsonify({
            'topics': isolated_topics,
            'functions': isolated_functions
        })
        
    except Exception as e:
        logger.error(f"Ошибка при получении изолированных элементов: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/hours-recommendations')
def get_hours_recommendations():
    try:
        config_id = request.args.get('configuration_id')
        discipline_id = request.args.get('discipline_id')
        similarity_type = request.args.get('similarity_type', 'rubert')
        
        if not config_id:
            return jsonify({'error': 'Configuration ID is required'}), 400
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Определяем поле сходства
        similarity_field = f"{similarity_type}_similarity"
        
        # Получаем статистику по часам для всех тем
        stats_query = '''
            WITH all_hours AS (
                SELECT lt.hours as topic_hours 
                FROM lecture_topics lt
                JOIN sections s ON lt.section_id = s.id
                JOIN similarity_results sr ON sr.topic_id = lt.id AND sr.topic_type = 'lecture'
                WHERE lt.hours IS NOT NULL
                AND sr.configuration_id = ?
        '''
        
        stats_params = [config_id]
        if discipline_id:
            stats_query += ' AND s.discipline_id = ?'
            stats_params.append(discipline_id)
            
        stats_query += '''
                UNION ALL
                SELECT pt.hours as topic_hours 
                FROM practical_topics pt
                JOIN sections s ON pt.section_id = s.id
                JOIN similarity_results sr ON sr.topic_id = pt.id AND sr.topic_type = 'practical'
                WHERE pt.hours IS NOT NULL
                AND sr.configuration_id = ?
        '''
        
        stats_params.append(config_id)
        if discipline_id:
            stats_query += ' AND s.discipline_id = ?'
            stats_params.append(discipline_id)
            
        stats_query += '''
            )
            SELECT 
                AVG(topic_hours) as avg_hours,
                MAX(topic_hours) as max_hours,
                MIN(topic_hours) as min_hours
            FROM all_hours
        '''
        
        cursor.execute(stats_query, stats_params)
        stats = cursor.fetchone()
        avg_hours = stats['avg_hours']
        
        # Получаем 75-й и 25-й процентили
        percentiles_query = '''
            WITH all_hours AS (
                SELECT lt.hours as topic_hours 
                FROM lecture_topics lt
                JOIN sections s ON lt.section_id = s.id
                JOIN similarity_results sr ON sr.topic_id = lt.id AND sr.topic_type = 'lecture'
                WHERE lt.hours IS NOT NULL
                AND sr.configuration_id = ?
        '''
        
        percentiles_params = [config_id]
        if discipline_id:
            percentiles_query += ' AND s.discipline_id = ?'
            percentiles_params.append(discipline_id)
            
        percentiles_query += '''
                UNION ALL
                SELECT pt.hours as topic_hours 
                FROM practical_topics pt
                JOIN sections s ON pt.section_id = s.id
                JOIN similarity_results sr ON sr.topic_id = pt.id AND sr.topic_type = 'practical'
                WHERE pt.hours IS NOT NULL
                AND sr.configuration_id = ?
        '''
        
        percentiles_params.append(config_id)
        if discipline_id:
            percentiles_query += ' AND s.discipline_id = ?'
            percentiles_params.append(discipline_id)
            
        percentiles_query += '''
            ),
            ordered_hours AS (
                SELECT topic_hours,
                       ROW_NUMBER() OVER (ORDER BY topic_hours) as row_num,
                       COUNT(*) OVER () as total_count
                FROM all_hours
            )
            SELECT 
                MAX(CASE WHEN row_num <= total_count * 0.75 THEN topic_hours END) as q3_hours,
                MAX(CASE WHEN row_num <= total_count * 0.25 THEN topic_hours END) as q1_hours
            FROM ordered_hours
        '''
        
        cursor.execute(percentiles_query, percentiles_params)
        percentiles = cursor.fetchone()
        q3_hours = percentiles['q3_hours']  # 75-й процентиль
        q1_hours = percentiles['q1_hours']  # 25-й процентиль
        
        # Получаем темы с рекомендациями
        topics_query = f'''
            WITH topic_stats AS (
                SELECT 
                    sr.topic_id,
                    sr.topic_type,
                    CASE 
                        WHEN sr.topic_type = 'lecture' THEN lt.name
                        ELSE pt.name
                    END as topic_name,
                    CASE 
                        WHEN sr.topic_type = 'lecture' THEN lt.hours
                        ELSE pt.hours
                    END as topic_hours,
                    MAX(sr.{similarity_field}) as max_similarity,
                    COUNT(DISTINCT sr.labor_function_id) as functions_count
                FROM similarity_results sr
                LEFT JOIN lecture_topics lt ON sr.topic_type = 'lecture' AND sr.topic_id = lt.id
                LEFT JOIN practical_topics pt ON sr.topic_type = 'practical' AND sr.topic_id = pt.id
                LEFT JOIN sections s ON (sr.topic_type = 'lecture' AND lt.section_id = s.id) 
                    OR (sr.topic_type = 'practical' AND pt.section_id = s.id)
                WHERE sr.configuration_id = ?
                AND sr.{similarity_field} IS NOT NULL
        '''
        
        topics_params = [config_id]
        
        if discipline_id:
            topics_query += ' AND s.discipline_id = ?'
            topics_params.append(discipline_id)
            
        topics_query += '''
                GROUP BY sr.topic_id, sr.topic_type, topic_name, topic_hours
            )
            SELECT 
                topic_id,
                topic_type,
                topic_name,
                topic_hours as hours,
                max_similarity,
                functions_count,
                CASE
                    WHEN topic_hours > ? AND max_similarity < 0.3 THEN 'high_hours_low_similarity'
                    WHEN topic_hours < ? AND max_similarity > 0.7 THEN 'low_hours_high_similarity'
                    WHEN topic_hours > ? AND functions_count = 0 THEN 'high_hours_no_functions'
                    WHEN topic_hours < ? AND functions_count > 3 THEN 'low_hours_many_functions'
                    ELSE NULL
                END as recommendation_type
            FROM topic_stats
            WHERE recommendation_type IS NOT NULL
            ORDER BY 
                CASE recommendation_type
                    WHEN 'high_hours_low_similarity' THEN 1
                    WHEN 'high_hours_no_functions' THEN 2
                    WHEN 'low_hours_high_similarity' THEN 3
                    WHEN 'low_hours_many_functions' THEN 4
                END,
                topic_hours DESC
        '''
        
        topics_params.extend([q3_hours, q1_hours, q3_hours, q1_hours])
        
        cursor.execute(topics_query, topics_params)
        
        recommendations = []
        for row in cursor.fetchall():
            recommendation = {
                'topic_id': row['topic_id'],
                'topic_type': row['topic_type'],
                'topic_name': row['topic_name'],
                'hours': row['hours'],
                'max_similarity': row['max_similarity'],
                'functions_count': row['functions_count'],
                'type': row['recommendation_type']
            }
            
            # Формируем текст рекомендации
            if recommendation['type'] == 'high_hours_low_similarity':
                recommendation['message'] = (
                    f"Тема '{recommendation['topic_name']}' ({recommendation['hours']} часов) "
                    f"имеет низкое сходство с трудовыми функциями (макс. {recommendation['max_similarity']:.2f}). "
                    "Рекомендуется пересмотреть содержание темы для лучшего соответствия профстандартам."
                )
            elif recommendation['type'] == 'high_hours_no_functions':
                recommendation['message'] = (
                    f"Тема '{recommendation['topic_name']}' ({recommendation['hours']} часов) "
                    "не имеет связей с трудовыми функциями. "
                    "Рекомендуется проверить актуальность темы или добавить связи с профстандартами."
                )
            elif recommendation['type'] == 'low_hours_high_similarity':
                recommendation['message'] = (
                    f"Тема '{recommendation['topic_name']}' ({recommendation['hours']} часов) "
                    f"имеет высокое сходство с трудовыми функциями (макс. {recommendation['max_similarity']:.2f}). "
                    "Рекомендуется увеличить количество часов для лучшего освоения компетенций."
                )
            elif recommendation['type'] == 'low_hours_many_functions':
                recommendation['message'] = (
                    f"Тема '{recommendation['topic_name']}' ({recommendation['hours']} часов) "
                    f"связана с {recommendation['functions_count']} трудовыми функциями. "
                    "Рекомендуется увеличить количество часов для лучшего освоения всех связанных компетенций."
                )
            
            recommendations.append(recommendation)
            
        conn.close()
        
        return jsonify({
            'recommendations': recommendations,
            'stats': {
                'avg_hours': avg_hours,
                'max_hours': stats['max_hours'],
                'min_hours': stats['min_hours'],
                'percentile_75': q3_hours,
                'percentile_25': q1_hours
            }
        })
        
    except Exception as e:
        logger.error(f"Ошибка при получении рекомендаций по часам: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 