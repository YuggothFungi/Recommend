-- Таблица конфигураций векторизации
CREATE TABLE IF NOT EXISTS vectorization_configurations (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    config_type TEXT NOT NULL CHECK (config_type IN ('l1_p1', 'l1l2_p1p2', 'l1l2l3_p1p2')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица весов для источников текста
CREATE TABLE IF NOT EXISTS vectorization_weights (
    id INTEGER PRIMARY KEY,
    configuration_id INTEGER NOT NULL,
    entity_type TEXT NOT NULL CHECK (entity_type IN ('lecture_topic', 'practical_topic', 'labor_function')),
    source_type TEXT NOT NULL,
    use_normalized BOOLEAN DEFAULT TRUE,
    weight REAL DEFAULT 1.0,
    hours_weight REAL DEFAULT 1.0,
    FOREIGN KEY (configuration_id) REFERENCES vectorization_configurations(id) ON DELETE CASCADE
);

-- Таблица результатов векторизации
CREATE TABLE IF NOT EXISTS vectorization_results (
    id INTEGER PRIMARY KEY,
    configuration_id INTEGER NOT NULL,
    entity_type TEXT NOT NULL CHECK (entity_type IN ('lecture_topic', 'practical_topic', 'labor_function')),
    entity_id INTEGER NOT NULL,
    vector_type TEXT NOT NULL CHECK (vector_type IN ('tfidf', 'rubert')),
    vector_data BLOB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (configuration_id) REFERENCES vectorization_configurations(id) ON DELETE CASCADE
);

-- Таблица результатов сходства
CREATE TABLE IF NOT EXISTS similarity_results (
    id INTEGER PRIMARY KEY,
    configuration_id INTEGER NOT NULL,
    topic_id INTEGER NOT NULL,
    topic_type TEXT NOT NULL CHECK (topic_type IN ('lecture', 'practical')),
    labor_function_id TEXT NOT NULL,
    rubert_similarity REAL NOT NULL,
    tfidf_similarity REAL NOT NULL,
    topic_hours REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (configuration_id) REFERENCES vectorization_configurations(id) ON DELETE CASCADE
);

-- Индексы для оптимизации запросов
CREATE INDEX IF NOT EXISTS idx_vectorization_weights_config 
ON vectorization_weights(configuration_id);

CREATE INDEX IF NOT EXISTS idx_vectorization_weights_entity 
ON vectorization_weights(entity_type);

CREATE INDEX IF NOT EXISTS idx_vectorization_results_config 
ON vectorization_results(configuration_id);

CREATE INDEX IF NOT EXISTS idx_vectorization_results_entity 
ON vectorization_results(entity_type, entity_id);

CREATE INDEX IF NOT EXISTS idx_similarity_results_config 
ON similarity_results(configuration_id);

CREATE INDEX IF NOT EXISTS idx_similarity_results_topic 
ON similarity_results(topic_type, topic_id);

CREATE INDEX IF NOT EXISTS idx_similarity_results_function 
ON similarity_results(labor_function_id);

-- Предопределенные конфигурации
INSERT OR IGNORE INTO vectorization_configurations (name, description, config_type) VALUES
('Только базовые сущности', 'Векторизация только названий тем и трудовых функций', 'l1_p1'),
('Базовые сущности + контекст раздела', 'Векторизация с учетом контекста раздела и компонентов', 'l1l2_p1p2'),
('Полный контекст', 'Векторизация с учетом полного контекста', 'l1l2l3_p1p2');

-- Веса для конфигурации l1_p1
INSERT OR IGNORE INTO vectorization_weights (configuration_id, entity_type, source_type, weight) VALUES
(1, 'lecture_topic', 'name', 1.0),
(1, 'practical_topic', 'name', 1.0),
(1, 'labor_function', 'name', 1.0);

-- Веса для конфигурации l1l2_p1p2
INSERT OR IGNORE INTO vectorization_weights (configuration_id, entity_type, source_type, weight) VALUES
(2, 'lecture_topic', 'name', 1.0),
(2, 'lecture_topic', 'section_name', 0.5),
(2, 'lecture_topic', 'section_content', 0.5),
(2, 'lecture_topic', 'self_control_questions', 0.3),
(2, 'practical_topic', 'name', 1.0),
(2, 'practical_topic', 'section_name', 0.5),
(2, 'practical_topic', 'section_content', 0.5),
(2, 'practical_topic', 'self_control_questions', 0.3),
(2, 'labor_function', 'name', 1.0),
(2, 'labor_function', 'labor_components', 0.7);

-- Веса для конфигурации l1l2l3_p1p2
INSERT OR IGNORE INTO vectorization_weights (configuration_id, entity_type, source_type, weight) VALUES
(3, 'lecture_topic', 'name', 1.0),
(3, 'lecture_topic', 'section_name', 0.5),
(3, 'lecture_topic', 'section_content', 0.5),
(3, 'lecture_topic', 'self_control_questions', 0.3),
(3, 'lecture_topic', 'discipline_goals', 0.3),
(3, 'lecture_topic', 'discipline_tasks', 0.3),
(3, 'practical_topic', 'name', 1.0),
(3, 'practical_topic', 'section_name', 0.5),
(3, 'practical_topic', 'section_content', 0.5),
(3, 'practical_topic', 'self_control_questions', 0.3),
(3, 'practical_topic', 'discipline_goals', 0.3),
(3, 'practical_topic', 'discipline_tasks', 0.3),
(3, 'labor_function', 'name', 1.0),
(3, 'labor_function', 'labor_components', 0.7); 