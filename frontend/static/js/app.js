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
            const response = await fetch(`/api/topics?discipline_id=${disciplineId}`);
            const topics = await response.json();
            
            // Очищаем и заполняем таблицу тем
            topicsTable.innerHTML = '';
            topics.forEach(topic => {
                const row = document.createElement('tr');
                row.dataset.id = topic.id;
                row.innerHTML = `
                    <td>${topic.title}</td>
                    <td>${topic.description || ''}</td>
                `;
                row.addEventListener('click', () => handleTopicClick(topic.id));
                topicsTable.appendChild(row);
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
            const response = await fetch(url);
            const data = await response.json();
            
            // Обновляем таблицу в зависимости от типа
            if (type === 'topic') {
                updateFunctionsTable(data.results);
            } else {
                updateTopicsTable(data.results);
            }
            
            // Обновляем рекомендации
            updateRecommendations(data.recommendations);
        } catch (error) {
            console.error('Ошибка при загрузке сходства:', error);
        }
    }

    // Функция обновления таблицы трудовых функций
    function updateFunctionsTable(results) {
        const rows = functionsTable.getElementsByTagName('tr');
        Array.from(rows).forEach(row => {
            const id = row.dataset.id;
            const similarityCell = row.cells[1];
            const result = results.find(r => r.id === parseInt(id));
            
            if (result) {
                similarityCell.textContent = result.similarity.toFixed(2);
                row.classList.add('highlighted');
            } else {
                similarityCell.textContent = '-';
                row.classList.remove('highlighted');
            }
        });
    }

    // Функция обновления таблицы тем
    function updateTopicsTable(results) {
        const rows = topicsTable.getElementsByTagName('tr');
        Array.from(rows).forEach(row => {
            const id = row.dataset.id;
            const similarityCell = row.insertCell(2) || row.cells[2];
            const result = results.find(r => r.id === parseInt(id));
            
            if (result) {
                similarityCell.textContent = result.similarity.toFixed(2);
                row.classList.add('highlighted');
            } else {
                similarityCell.textContent = '-';
                row.classList.remove('highlighted');
            }
        });
    }

    // Функция обновления рекомендаций
    function updateRecommendations(recommendations) {
        recommendationsDiv.innerHTML = '';
        recommendations.forEach(rec => {
            const div = document.createElement('div');
            div.textContent = rec;
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
            const prevRow = topicsTable.querySelector(`tr[data-id="${selectedTopicId}"]`);
            if (prevRow) prevRow.classList.remove('selected');
        }
        
        // Выделяем новую тему
        const row = topicsTable.querySelector(`tr[data-id="${topicId}"]`);
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