document.addEventListener('DOMContentLoaded', function() {
    console.log('Frontend application started');
    // Получаем элементы DOM
    const disciplineSelect = document.getElementById('discipline');
    const thresholdSlider = document.getElementById('threshold');
    const thresholdValue = document.getElementById('threshold-value');
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

    // Функция загрузки дисциплин
    async function loadDisciplines() {
        try {
            const response = await fetch('/api/disciplines');
            const disciplines = await response.json();
            
            // Очищаем и заполняем выпадающий список
            disciplineSelect.innerHTML = '<option value="">Выберите дисциплину...</option>';
            disciplines.forEach(discipline => {
                const option = document.createElement('option');
                option.value = discipline.id;
                option.textContent = discipline.name;
                disciplineSelect.appendChild(option);
            });
        } catch (error) {
            console.error('Ошибка при загрузке дисциплин:', error);
        }
    }

    // Функция загрузки тем по выбранной дисциплине
    async function loadTopics(disciplineId) {
        try {
            console.log('Загрузка тем для дисциплины:', disciplineId);
            const response = await fetch(`/api/topics?discipline_id=${disciplineId}`);
            console.log('Ответ от сервера:', response);
            const topics = await response.json();
            console.log('Полученные темы:', topics);
            
            // Очищаем и заполняем таблицу тем
            const tbody = document.querySelector('#topics-table tbody');
            tbody.innerHTML = '';
            
            topics.forEach(topic => {
                const tr = document.createElement('tr');
                tr.dataset.topicId = topic.id;
                tr.innerHTML = `
                    <td>${topic.name}</td>
                    <td>${topic.description || ''}</td>
                    <td>${topic.hours || '-'}</td>
                    <td class="similarity">${typeof topic.similarity === 'number' ? topic.similarity.toFixed(2) : '-'}</td>
                `;
                tr.addEventListener('click', () => handleTopicClick(topic.id));
                tbody.appendChild(tr);
            });
        } catch (error) {
            console.error('Ошибка при загрузке тем:', error);
        }
    }

    // Функция загрузки трудовых функций
    async function loadLaborFunctions() {
        try {
            const response = await fetch('/api/labor_functions');
            const functions = await response.json();
            
            // Очищаем и заполняем таблицу функций
            functionsTable.innerHTML = '';
            functions.forEach(func => {
                const row = document.createElement('tr');
                row.dataset.id = func.id;
                row.innerHTML = `
                    <td>${func.name}</td>
                    <td>-</td>
                `;
                row.addEventListener('click', () => handleFunctionClick(func.id));
                functionsTable.appendChild(row);
            });
        } catch (error) {
            console.error('Ошибка при загрузке трудовых функций:', error);
        }
    }

    // Функция загрузки сходства и рекомендаций
    async function loadSimilarities(id, type) {
        const threshold = thresholdSlider.value / 100;
        const url = `/api/similarities?${type}_id=${id}&threshold=${threshold}`;
        try {
            console.log('Загрузка сходства:', { id, type, threshold, url });
            const response = await fetch(url);
            const data = await response.json();
            console.log('Полученные данные:', data);
            // Проверяем наличие рекомендации
            let highlightAllLow = false;
            let recommendations = data.recommendations || [];
            if (type === 'labor_function' && (!data.results || data.results.length === 0)) {
                recommendations = ['Для выбранной трудовой функции нет подходящих тем'];
                highlightAllLow = true;
            } else if (data.recommendations && data.recommendations.some(r => r.includes('Тема не обеспечивает трудовые функции'))) {
                highlightAllLow = true;
            }
            if (type === 'topic') {
                updateFunctionsTable(data.results);
            } else {
                updateTopicsTable(data.results, highlightAllLow);
            }
            updateRecommendations(recommendations);
        } catch (error) {
            console.error('Ошибка при загрузке сходства:', error);
        }
    }

    // Функция обновления таблицы трудовых функций
    function updateFunctionsTable(results) {
        // Сортируем по similarity по убыванию, элементы без similarity внизу
        const sortedResults = [...results].sort((a, b) => {
            if (typeof b.similarity === 'number' && typeof a.similarity === 'number') {
                return b.similarity - a.similarity;
            } else if (typeof b.similarity === 'number') {
                return 1;
            } else if (typeof a.similarity === 'number') {
                return -1;
            } else {
                return 0;
            }
        });
        functionsTable.innerHTML = '';
        sortedResults.forEach(func => {
            const row = document.createElement('tr');
            row.dataset.id = func.id;
            row.innerHTML = `
                <td>${func.name}</td>
                <td>${typeof func.similarity === 'number' ? func.similarity.toFixed(2) : '-'}</td>
            `;
            // Подсвечиваем только выбранную функцию (голубым)
            if (String(func.id) === String(selectedFunctionId)) {
                row.classList.add('selected');
            }
            // Бледно-розовая подсветка для низкого similarity или его отсутствия
            if (typeof func.similarity !== 'number' || func.similarity < 0.1) {
                row.classList.add('low-similarity');
            }
            row.addEventListener('click', () => handleFunctionClick(func.id));
            functionsTable.appendChild(row);
        });
    }

    // Функция обновления таблицы тем
    function updateTopicsTable(topics, highlightAllLow = false) {
        // Сортируем по similarity по убыванию, элементы без similarity внизу
        const sortedTopics = [...topics].sort((a, b) => {
            if (typeof b.similarity === 'number' && typeof a.similarity === 'number') {
                return b.similarity - a.similarity;
            } else if (typeof b.similarity === 'number') {
                return 1;
            } else if (typeof a.similarity === 'number') {
                return -1;
            } else {
                return 0;
            }
        });
        const tbody = document.querySelector('#topics-table tbody');
        tbody.innerHTML = '';
        sortedTopics.forEach(topic => {
            const tr = document.createElement('tr');
            tr.dataset.topicId = topic.id;
            tr.innerHTML = `
                <td>${topic.name}</td>
                <td>${topic.description}</td>
                <td>${topic.hours || '-'}</td>
                <td class="similarity">${typeof topic.similarity === 'number' ? topic.similarity.toFixed(2) : '-'}</td>
            `;
            // Подсвечиваем только выбранную тему (голубым)
            if (String(topic.id) === String(selectedTopicId)) {
                tr.classList.add('selected');
            }
            // Бледно-розовая подсветка для низкого similarity или его отсутствия, либо если highlightAllLow=true
            if (highlightAllLow || typeof topic.similarity !== 'number' || topic.similarity < 0.1) {
                tr.classList.add('low-similarity');
            }
            tr.addEventListener('click', () => handleTopicClick(topic.id));
            tbody.appendChild(tr);
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
        recommendationsDiv.innerHTML = '';
        recommendations.forEach(rec => {
            const div = document.createElement('div');
            div.textContent = rec;
            if (
                rec.includes('Тема не обеспечивает трудовые функции') ||
                rec.includes('Для выбранной трудовой функции нет подходящих тем')
            ) {
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
            loadSimilarities(selectedTopicId, 'topic');
        } else if (selectedFunctionId) {
            loadSimilarities(selectedFunctionId, 'labor_function');
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
        loadSimilarities(topicId, 'topic');
    }

    function handleFunctionClick(functionId) {
        // Снимаем выделение с предыдущей выбранной функции
        if (selectedFunctionId) {
            const prevRow = functionsTable.querySelector(`tr[data-id="${selectedFunctionId}"]`);
            if (prevRow) prevRow.classList.remove('selected');
        }
        
        // Выделяем новую функцию
        const row = functionsTable.querySelector(`tr[data-id="${functionId}"]`);
        if (row) row.classList.add('selected');
        
        selectedFunctionId = functionId;
        selectedTopicId = null;
        loadSimilarities(functionId, 'labor_function');
    }
}); 