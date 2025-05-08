document.addEventListener('DOMContentLoaded', function() {
    console.log('Frontend application started');
    // Получаем элементы DOM
    const disciplineSelect = document.getElementById('discipline');
    const thresholdSlider = document.getElementById('threshold');
    const thresholdValue = document.getElementById('threshold-value');
    const similarityTypeSelect = document.getElementById('similarity-type');
    const topicsTable = document.getElementById('topics-table').getElementsByTagName('tbody')[0];
    const functionsTable = document.getElementById('functions-table').getElementsByTagName('tbody')[0];
    const recommendationsDiv = document.getElementById('recommendations');

    // Текущие выбранные элементы
    let selectedTopicId = null;
    let selectedFunctionId = null;

    // Загрузка дисциплин при старте
    loadDisciplines();

    // Обработчики событий
    disciplineSelect.addEventListener('change', handleDisciplineChange);
    thresholdSlider.addEventListener('input', handleThresholdChange);
    similarityTypeSelect.addEventListener('change', handleSimilarityTypeChange);

    // Функция для логирования
    function log(message, data = null) {
        console.log(`[${new Date().toISOString()}] ${message}`, data || '');
    }

    // Функция загрузки дисциплин
    async function loadDisciplines() {
        try {
            log('Загрузка дисциплин...');
            const response = await fetch('/api/disciplines');
            log('Ответ от сервера:', response);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const disciplines = await response.json();
            log('Полученные дисциплины:', disciplines);
            
            disciplineSelect.innerHTML = '<option value="">Выберите дисциплину</option>';
            disciplines.forEach(discipline => {
                const option = document.createElement('option');
                option.value = discipline.id;
                option.textContent = discipline.name;
                disciplineSelect.appendChild(option);
            });
        } catch (error) {
            log('Ошибка при загрузке дисциплин:', error);
            alert('Ошибка при загрузке дисциплин');
        }
    }

    // Функция загрузки тем по выбранной дисциплине
    async function loadTopics(disciplineId) {
        try {
            log('Загрузка тем для дисциплины:', disciplineId);
            const response = await fetch(`/api/topics?discipline_id=${disciplineId}`);
            log('Ответ от сервера:', response);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const topics = await response.json();
            log('Полученные темы:', topics);
            
            if (!Array.isArray(topics)) {
                throw new Error('Полученные данные не являются массивом');
            }
            
            updateTopicsTable(topics);
        } catch (error) {
            log('Ошибка при загрузке тем:', error);
            alert('Ошибка при загрузке тем');
        }
    }

    // Функция загрузки трудовых функций
    async function loadLaborFunctions() {
        try {
            log('Загрузка всех трудовых функций');
            const response = await fetch('/api/labor-functions');
            log('Ответ от сервера:', response);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const functions = await response.json();
            log('Полученные трудовые функции:', functions);
            
            updateFunctionsTable(functions);
        } catch (error) {
            log('Ошибка при загрузке трудовых функций:', error);
            alert('Ошибка при загрузке трудовых функций');
        }
    }

    // Функция загрузки сходства и рекомендаций
    async function loadSimilarities(topicId) {
        try {
            const threshold = thresholdSlider.value / 100;
            const similarityType = similarityTypeSelect.value;
            
            log('Загрузка сходства для темы:', { topicId, threshold, similarityType });
            const response = await fetch(`/api/similarities?topic_id=${topicId}&threshold=${threshold}&similarity_type=${similarityType}`);
            log('Ответ от сервера:', response);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            log('Полученные данные о сходстве:', data);
            
            let recommendations = data.recommendations || [];
            
            if (!data.similarities || data.similarities.length === 0) {
                recommendations = ['Для выбранной трудовой функции нет подходящих тем'];
            } else if (data.recommendations && data.recommendations.some(r => r.includes('Тема не обеспечивает трудовые функции'))) {
                recommendations = ['Тема не обеспечивает трудовые функции'];
            }
            
            updateRecommendations(recommendations);
        } catch (error) {
            log('Ошибка при загрузке сходства:', error);
            alert('Ошибка при загрузке сходства');
        }
    }

    // Функция обновления таблицы трудовых функций
    function updateFunctionsTable(functions) {
        log('Обновление таблицы трудовых функций:', functions);
        functionsTable.innerHTML = '';
        functions.forEach(func => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td style="width: 100%; white-space: normal;">${func.name}</td>
                <td style="min-width: 60px; max-width: 80px;">-</td>
            `;
            functionsTable.appendChild(row);
        });
    }

    // Функция обновления таблицы тем
    function updateTopicsTable(topics) {
        log('Обновление таблицы тем:', topics);
        // Очищаем только тело таблицы (tbody)
        topicsTable.innerHTML = '';
        // Добавляем все темы без фильтрации
        topics.forEach(topic => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td style="min-width: 40px; max-width: 60px;">${topic.type === 'lecture' ? 'Л' : 'П'}</td>
                <td style="width: 100%; white-space: normal;">${topic.name}</td>
                <td style="min-width: 40px; max-width: 60px;">${topic.hours !== null && topic.hours !== undefined ? topic.hours : '-'}</td>
                <td style="min-width: 60px; max-width: 80px;">-</td>
            `;
            row.onclick = () => loadSimilarities(topic.id);
            topicsTable.appendChild(row);
        });
    }

    function updateSimilarities(similarities) {
        // Обновляем значения сходства в таблице тем
        const topicRows = document.querySelectorAll('#topics-table tbody tr');
        topicRows.forEach(row => {
            const similarityCell = row.querySelector('.similarity');
            const topicId = parseInt(row.dataset.topicId);
            const similarity = similarities.find(s => s.topic_id === topicId);
            similarityCell.textContent = similarity ? similarity.score.toFixed(2) : '-';
        });

        // Обновляем значения сходства в таблице функций
        const functionRows = document.querySelectorAll('#functions-table tbody tr');
        functionRows.forEach(row => {
            const similarityCell = row.querySelector('.similarity');
            const functionId = parseInt(row.dataset.functionId);
            const similarity = similarities.find(s => s.function_id === functionId);
            similarityCell.textContent = similarity ? similarity.score.toFixed(2) : '-';
        });
    }

    // Функция обновления рекомендаций
    function updateRecommendations(recommendations) {
        log('Обновление рекомендаций:', recommendations);
        recommendationsDiv.innerHTML = '';
        recommendations.forEach(rec => {
            const div = document.createElement('div');
            div.textContent = rec;
            if (rec.includes('не обеспечивает') || rec.includes('нет подходящих')) {
                div.classList.add('recommendation-warning');
            }
            recommendationsDiv.appendChild(div);
        });
    }

    // Обработчики событий
    function handleDisciplineChange() {
        const disciplineId = disciplineSelect.value;
        if (disciplineId) {
            loadTopics(disciplineId);
            loadLaborFunctions();
        } else {
            topicsTable.innerHTML = '';
            functionsTable.innerHTML = '';
            recommendationsDiv.innerHTML = '';
        }
    }

    function handleThresholdChange() {
        const value = (thresholdSlider.value / 100).toFixed(2);
        thresholdValue.textContent = value;
        
        if (selectedTopicId) {
            loadSimilarities(selectedTopicId);
        } else if (selectedFunctionId) {
            loadSimilarities(selectedFunctionId);
        }
    }

    function handleSimilarityTypeChange() {
        if (selectedTopicId) {
            loadSimilarities(selectedTopicId);
        } else if (selectedFunctionId) {
            loadSimilarities(selectedFunctionId);
        }
    }

    function handleTopicClick(topicId) {
        // Снимаем выделение с предыдущей выбранной темы
        if (selectedTopicId) {
            const prevRow = document.querySelector(`#topics-table tr[data-topic-id="${selectedTopicId}"]`);
            if (prevRow) prevRow.classList.remove('selected');
        }
        
        // Выделяем новую тему
        const row = document.querySelector(`#topics-table tr[data-topic-id="${topicId}"]`);
        if (row) row.classList.add('selected');
        
        selectedTopicId = topicId;
        selectedFunctionId = null;
        loadSimilarities(topicId);
    }

    function handleFunctionClick(functionId) {
        // Снимаем выделение с предыдущей выбранной функции
        if (selectedFunctionId) {
            const prevRow = document.querySelector(`#functions-table tr[data-id="${selectedFunctionId}"]`);
            if (prevRow) prevRow.classList.remove('selected');
        }
        
        // Выделяем новую функцию
        const row = document.querySelector(`#functions-table tr[data-id="${functionId}"]`);
        if (row) row.classList.add('selected');
        
        selectedFunctionId = functionId;
        selectedTopicId = null;
        loadSimilarities(functionId);
    }

    // Инициализация
    log('Инициализация приложения...');
    loadDisciplines();
}); 