import os
import sys

# Добавляем корневую директорию в PYTHONPATH
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)

from flask import Flask, render_template, jsonify, request

# Импортируем db.py напрямую
import src.db as db

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/disciplines')
def get_disciplines():
    """Получение списка всех дисциплин"""
    conn = db.get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, name 
        FROM disciplines 
        ORDER BY name
    """)
    disciplines = [{"id": row[0], "name": row[1]} for row in cursor.fetchall()]
    
    conn.close()
    return jsonify(disciplines)

@app.route('/api/topics')
def get_topics():
    """Получение тем по выбранной дисциплине"""
    discipline_id = request.args.get('discipline_id')
    if not discipline_id:
        return jsonify({"error": "discipline_id is required"}), 400
    
    conn = db.get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, title, description 
        FROM topics 
        WHERE discipline_id = ?
        ORDER BY title
    """, (discipline_id,))
    
    topics = [{
        "id": row[0],
        "title": row[1],
        "description": row[2]
    } for row in cursor.fetchall()]
    
    conn.close()
    return jsonify(topics)

@app.route('/api/labor_functions')
def get_labor_functions():
    """Получение списка всех трудовых функций"""
    conn = db.get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, name 
        FROM labor_functions 
        ORDER BY name
    """)
    
    functions = [{"id": row[0], "name": row[1]} for row in cursor.fetchall()]
    
    conn.close()
    return jsonify(functions)

@app.route('/api/similarities')
def get_similarities():
    """Получение сходства между темами и трудовыми функциями"""
    topic_id = request.args.get('topic_id')
    labor_function_id = request.args.get('labor_function_id')
    threshold = float(request.args.get('threshold', 0.5))
    
    if not (topic_id or labor_function_id):
        return jsonify({"error": "either topic_id or labor_function_id is required"}), 400
    
    conn = db.get_db_connection()
    cursor = conn.cursor()
    
    if topic_id:
        # Получаем релевантные трудовые функции для темы
        cursor.execute("""
            SELECT lf.id, lf.name, tlf.rubert_similarity
            FROM topic_labor_function tlf
            JOIN labor_functions lf ON lf.id = tlf.labor_function_id
            WHERE tlf.topic_id = ? AND tlf.rubert_similarity >= ?
            ORDER BY tlf.rubert_similarity DESC
        """, (topic_id, threshold))
        
        results = [{
            "id": row[0],
            "name": row[1],
            "similarity": row[2]
        } for row in cursor.fetchall()]
        
        # Получаем рекомендации для темы
        recommendations = []
        if not results:
            recommendations.append("Тема не обеспечивает трудовые функции")
        else:
            # Проверяем среднее сходство
            avg_similarity = sum(r["similarity"] for r in results) / len(results)
            if avg_similarity < 0.7:
                recommendations.append("Рекомендуется уделить больше времени для изучения темы")
            
            # Проверяем разницу между ruBERT и TF-IDF
            cursor.execute("""
                SELECT AVG(tfidf_similarity)
                FROM topic_labor_function
                WHERE topic_id = ?
            """, (topic_id,))
            avg_tfidf = cursor.fetchone()[0] or 0
            
            if avg_similarity > 0.8 and avg_tfidf < 0.3:
                recommendations.append("Возможно требуется перефразирование темы для лучшего текстового сходства")
            
            if avg_similarity > 0.8:
                recommendations.append("Тема хорошо удовлетворяет трудовым функциям")
    
    else:
        # Получаем релевантные темы для трудовой функции
        cursor.execute("""
            SELECT t.id, t.title, tlf.rubert_similarity
            FROM topic_labor_function tlf
            JOIN topics t ON t.id = tlf.topic_id
            WHERE tlf.labor_function_id = ? AND tlf.rubert_similarity >= ?
            ORDER BY tlf.rubert_similarity DESC
        """, (labor_function_id, threshold))
        
        results = [{
            "id": row[0],
            "title": row[1],
            "similarity": row[2]
        } for row in cursor.fetchall()]
        
        recommendations = []
    
    conn.close()
    return jsonify({
        "results": results,
        "recommendations": recommendations
    })

if __name__ == '__main__':
    app.run(debug=True) 