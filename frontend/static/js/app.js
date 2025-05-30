document.addEventListener('DOMContentLoaded', function() {
    console.log('Frontend application started');
    // Получаем элементы DOM
    const disciplineSelect = document.getElementById('discipline');
    const thresholdSlider = document.getElementById('threshold');
    const thresholdValue = document.getElementById('threshold-value');
    const similarityTypeSelect = document.getElementById('similarity-type');
    const configurationSelect = document.getElementById('configuration-id');
    const topicsTable = document.getElementById('topics-table').getElementsByTagName('tbody')[0];
    const functionsTable = document.getElementById('functions-table').getElementsByTagName('tbody')[0];
    const recommendationsDiv = document.getElementById('recommendations');

    // Текущие выбранные элементы
    let selectedTopicId = null;
    let selectedFunctionId = null;

    // Глобальные переменные для хранения выбранной строки
    let selectedRow = null;
    let selectedType = null; // 'topic' или 'function'

    // Загрузка дисциплин при старте
    loadDisciplines();
    loadConfigurations();

    // Обработчики событий
    disciplineSelect.addEventListener('change', handleDisciplineChange);
    thresholdSlider.addEventListener('input', handleThresholdChange);
    similarityTypeSelect.addEventListener('change', handleSimilarityTypeChange);
    configurationSelect.addEventListener('change', () => {
        log('Изменена конфигурация:', configurationSelect.value);
        // Если выбрана тема, обновить таблицу функций
        if (selectedTopicId) {
            loadSimilarities(selectedTopicId);
        }
    });

    // Обработчик переключения вкладок
    const tabButtons = document.querySelectorAll('.tab-button');
    tabButtons.forEach(button => {
        button.addEventListener('click', async () => {
            // Убираем активный класс у всех кнопок и вкладок
            tabButtons.forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.tab-pane').forEach(pane => pane.classList.remove('active'));
            
            // Добавляем активный класс выбранной кнопке и соответствующей вкладке
            button.classList.add('active');
            const tabId = button.getAttribute('data-tab');
            document.getElementById(tabId).classList.add('active');

            // Загружаем данные в зависимости от выбранной вкладки
            const configId = document.getElementById('configuration-id').value;
            if (!configId) {
                alert('Пожалуйста, выберите конфигурацию');
                return;
            }

            try {
                if (tabId === 'keywords') {
                    if (!selectedRow) {
                        document.getElementById('keywords-list').innerHTML = '<div class="no-items">Выберите тему или функцию для просмотра ключевых слов</div>';
                        return;
                    }

                    // Получаем ID выбранной сущности
                    const entityId = selectedType === 'topic' ? selectedTopicId : selectedFunctionId;
                    
                    // Определяем тип сущности
                    let entityType;
                    if (selectedType === 'topic') {
                        // Получаем тип темы из строки таблицы
                        const typeCell = selectedRow.cells[0];
                        entityType = typeCell.textContent.trim() === 'Л' ? 'lecture_topic' : 'practical_topic';
                    } else {
                        entityType = 'labor_function';
                    }
                    
                    const response = await fetch(`/api/keywords?entity_id=${entityId}&entity_type=${entityType}&config_id=${configId}`);
                    const data = await response.json();
                    
                    if (data.error) {
                        throw new Error(data.error);
                    }
                    
                    // Отображаем ключевые слова
                    const keywordsList = document.getElementById('keywords-list');
                    if (data.keywords && data.keywords.length > 0) {
                        keywordsList.innerHTML = data.keywords.map(kw => `
                            <div class="keyword-item">
                                ${kw.keyword}
                                <span class="keyword-weight">(${kw.weight.toFixed(2)})</span>
                            </div>
                        `).join('');
                    } else {
                        keywordsList.innerHTML = '<div class="no-items">Нет ключевых слов для отображения</div>';
                    }
                } else if (tabId === 'isolated') {
                    const threshold = document.getElementById('threshold').value / 100;
                    const similarityType = document.getElementById('similarity-type').value;
                    const disciplineId = document.getElementById('discipline').value;
                    
                    const params = new URLSearchParams({
                        configuration_id: configId,
                        threshold: threshold,
                        similarity_type: similarityType
                    });
                    
                    if (disciplineId) {
                        params.append('discipline_id', disciplineId);
                    }
                    
                    const response = await fetch(`/api/isolated-elements?${params.toString()}`);
                    const data = await response.json();
                    
                    if (data.error) {
                        throw new Error(data.error);
                    }
                    
                    // Отображаем изолированные темы
                    const topicsContainer = document.getElementById('isolated-topics');
                    if (data.topics && data.topics.length > 0) {
                        topicsContainer.innerHTML = data.topics.map(topic => `
                            <div class="isolated-item">
                                <span class="item-name">${topic.name}</span>
                                <span class="item-type">${topic.type === 'lecture' ? 'Лекция' : 'Практика'}</span>
                                <span class="item-similarity">${topic.max_similarity ? topic.max_similarity.toFixed(2) : 'Нет данных'}</span>
                            </div>
                        `).join('');
                    } else {
                        topicsContainer.innerHTML = '<div class="no-items">Нет изолированных тем</div>';
                    }
                    
                    // Отображаем изолированные функции
                    const functionsContainer = document.getElementById('isolated-functions');
                    if (data.functions && data.functions.length > 0) {
                        functionsContainer.innerHTML = data.functions.map(func => `
                            <div class="isolated-item">
                                <span class="item-name">${func.name}</span>
                                <span class="item-similarity">${func.max_similarity ? func.max_similarity.toFixed(2) : 'Нет данных'}</span>
                            </div>
                        `).join('');
                    } else {
                        functionsContainer.innerHTML = '<div class="no-items">Нет изолированных функций</div>';
                    }
                }
            } catch (error) {
                console.error('Ошибка при загрузке данных:', error);
                alert('Произошла ошибка при загрузке данных: ' + error.message);
            }
        });
    });

    // Обработчик клика по строке в таблице тем
    topicsTable.addEventListener('click', function(e) {
        const row = e.target.closest('tr');
        if (!row) return;
        
        // Убираем выделение с предыдущей выбранной строки
        if (selectedRow) {
            selectedRow.classList.remove('selected');
        }
        
        // Выделяем новую строку
        row.classList.add('selected');
        selectedRow = row;
        selectedType = 'topic';
        
        // Сохраняем ID темы
        selectedTopicId = row.dataset.id;
        selectedFunctionId = null;
        
        // Загружаем сходство и рекомендации
        loadSimilarities(selectedTopicId);
        loadSimilarityComparison(selectedTopicId);
    });

    // Обработчик клика по строке в таблице функций
    functionsTable.addEventListener('click', function(e) {
        const row = e.target.closest('tr');
        if (!row) return;
        
        // Убираем выделение с предыдущей выбранной строки
        if (selectedRow) {
            selectedRow.classList.remove('selected');
        }
        
        // Выделяем новую строку
        row.classList.add('selected');
        selectedRow = row;
        selectedType = 'function';
        
        // Сохраняем ID функции
        selectedFunctionId = row.dataset.id;
        selectedTopicId = null;
        
        // Загружаем темы для выбранной функции
        loadTopicsByFunction(selectedFunctionId);
    });

    // Обработчик для кнопки "Найти рекомендации"
    document.getElementById('find-recommendations').addEventListener('click', async function() {
        const configId = document.getElementById('configuration-id').value;
        const disciplineId = document.getElementById('discipline').value;
        const similarityType = document.getElementById('similarity-type').value;

        if (!configId || !disciplineId) {
            alert('Пожалуйста, выберите конфигурацию и дисциплину');
            return;
        }

        try {
            // Загружаем текстовые формулировки
            const response = await fetch(`/api/recommendations?config_id=${configId}&discipline_id=${disciplineId}&similarity_type=${similarityType}`);
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }

            // Отображаем текстовые формулировки
            const textFormulations = document.getElementById('text-formulations');
            textFormulations.innerHTML = '';
            
            if (data.recommendations && data.recommendations.length > 0) {
                data.recommendations.forEach(rec => {
                    const div = document.createElement('div');
                    div.className = rec.type === 'warning' ? 'recommendation-warning' : 'recommendation-info';
                    div.textContent = rec.message;
                    textFormulations.appendChild(div);
                });
            } else {
                textFormulations.innerHTML = '<div class="recommendation-info">Нет рекомендаций для отображения</div>';
            }

            // Загружаем ключевые слова
            const keywordsResponse = await fetch(`/api/keywords?config_id=${configId}&discipline_id=${disciplineId}`);
            const keywordsData = await keywordsResponse.json();
            
            const keywordsContainer = document.getElementById('keywords');
            keywordsContainer.innerHTML = '';
            
            if (keywordsData.keywords && keywordsData.keywords.length > 0) {
                keywordsData.keywords.forEach(keyword => {
                    const div = document.createElement('div');
                    div.className = 'keyword-item';
                    div.innerHTML = `
                        <span>${keyword.word}</span>
                        <span class="keyword-weight">${keyword.weight.toFixed(2)}</span>
                    `;
                    keywordsContainer.appendChild(div);
                });
            } else {
                keywordsContainer.innerHTML = '<div class="no-items">Нет ключевых слов для отображения</div>';
            }

            // Загружаем изолированные элементы
            const isolatedResponse = await fetch(`/api/isolated?config_id=${configId}&discipline_id=${disciplineId}&similarity_type=${similarityType}`);
            const isolatedData = await isolatedResponse.json();
            
            const isolatedContainer = document.getElementById('isolated');
            isolatedContainer.innerHTML = '';
            
            if (isolatedData.sections && isolatedData.sections.length > 0) {
                isolatedData.sections.forEach(section => {
                    const sectionDiv = document.createElement('div');
                    sectionDiv.className = 'isolated-section';
                    sectionDiv.innerHTML = `<h3>${section.name}</h3>`;
                    
                    if (section.items && section.items.length > 0) {
                        section.items.forEach(item => {
                            const itemDiv = document.createElement('div');
                            itemDiv.className = 'isolated-item';
                            itemDiv.innerHTML = `
                                <span class="item-name">${item.name}</span>
                                <span class="item-type">${item.type}</span>
                                <span class="item-similarity">${item.similarity.toFixed(2)}</span>
                            `;
                            sectionDiv.appendChild(itemDiv);
                        });
                    } else {
                        sectionDiv.innerHTML += '<div class="no-items">Нет изолированных элементов</div>';
                    }
                    
                    isolatedContainer.appendChild(sectionDiv);
                });
            } else {
                isolatedContainer.innerHTML = '<div class="no-items">Нет изолированных элементов для отображения</div>';
            }

            // Активируем вкладку с текстовыми формулировками
            document.querySelector('[data-tab="text-formulations"]').click();

        } catch (error) {
            console.error('Ошибка при загрузке рекомендаций:', error);
            alert('Произошла ошибка при загрузке рекомендаций: ' + error.message);
        }
    });

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

    // Функция загрузки конфигураций
    async function loadConfigurations() {
        try {
            log('Загрузка конфигураций...');
            const response = await fetch('/api/configurations');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const configs = await response.json();
            log('Полученные конфигурации:', configs);
            configurationSelect.innerHTML = '';
            configs.forEach(cfg => {
                const option = document.createElement('option');
                option.value = cfg.id;
                option.textContent = cfg.name;
                option.title = cfg.description || '';
                configurationSelect.appendChild(option);
            });
            if (configs.length === 0) {
                const option = document.createElement('option');
                option.value = '';
                option.textContent = 'Нет конфигураций';
                configurationSelect.appendChild(option);
            }
        } catch (error) {
            log('Ошибка при загрузке конфигураций:', error);
            configurationSelect.innerHTML = '<option value="">Ошибка загрузки</option>';
        }
    }

    // Функция загрузки сходства и подходящих трудовых функций
    async function loadSimilarities(topicId) {
        try {
            const threshold = thresholdSlider.value / 100;
            const similarityType = similarityTypeSelect.value;
            const configurationId = configurationSelect.value;
            log('Загрузка сходства для темы:', { topicId, threshold, similarityType, configurationId });
            const response = await fetch(`/api/similarities?topic_id=${topicId}&threshold=${threshold}&similarity_type=${similarityType}&configuration_id=${configurationId}`);
            log('Ответ от сервера:', response);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            log('Полученные данные о сходстве:', data);
            // Обновляем таблицу функций только подходящими функциями
            if (data.functions && Array.isArray(data.functions)) {
                updateFunctionsTable(data.functions);
            } else {
                updateFunctionsTable([]);
            }
        } catch (error) {
            log('Ошибка при загрузке сходства:', error);
            alert('Ошибка при загрузке сходства');
        }
    }

    // Функция загрузки сравнения сходства и рекомендаций
    async function loadSimilarityComparison(topicId) {
        try {
            log('Загрузка сравнения сходства для темы:', topicId);
            const url = `/api/similarity-comparison?topic_id=${topicId}`;
            log('URL запроса:', url);
            
            const response = await fetch(url);
            log('Статус ответа:', response.status);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            log('Полученные данные сравнения:', data);
            
            if (data.error) {
                log('Ошибка от сервера:', data.error);
                return;
            }
            
            if (data.recommendations && Array.isArray(data.recommendations)) {
                log('Количество рекомендаций:', data.recommendations.length);
                log('Рекомендации:', data.recommendations);
                updateRecommendations(data.recommendations);
            } else {
                log('Нет рекомендаций в ответе');
                updateRecommendations([]);
            }
        } catch (error) {
            log('Ошибка при загрузке сравнения сходства:', error);
            alert('Ошибка при загрузке сравнения сходства');
        }
    }

    // Модифицируем updateFunctionsTable для выделения выбранной строки и дефиса в сходстве
    function updateFunctionsTable(functions) {
        log('Обновление таблицы трудовых функций:', functions);
        functionsTable.innerHTML = '';
        if (!functions || functions.length === 0) {
            const row = document.createElement('tr');
            row.innerHTML = `<td colspan="2" style="text-align:center; color:#888;">Нет подходящих функций</td>`;
            functionsTable.appendChild(row);
            return;
        }
        functions.forEach(func => {
            const row = document.createElement('tr');
            row.dataset.id = func.id;
            row.innerHTML = `
                <td style="width: 100%; white-space: normal;">${func.name}</td>
                <td style="min-width: 60px; max-width: 80px;">${selectedFunctionId === func.id ? '-' : (typeof func.similarity === 'number' ? func.similarity.toFixed(2) : '-')}</td>
            `;
            if (selectedFunctionId === func.id) row.classList.add('selected');
            row.onclick = () => {
                selectedFunctionId = func.id;
                selectedTopicId = null;
                // Снимаем выделение со всех строк
                Array.from(functionsTable.children).forEach(r => r.classList.remove('selected'));
                row.classList.add('selected');
                loadTopicsByFunction(func.id);
            };
            functionsTable.appendChild(row);
        });
    }

    // Функция загрузки тем по выбранной функции
    async function loadTopicsByFunction(functionId) {
        try {
            const threshold = thresholdSlider.value / 100;
            const similarityType = similarityTypeSelect.value;
            const configurationId = configurationSelect.value;
            const disciplineId = disciplineSelect.value;
            
            log('Загрузка тем для функции:', { functionId, threshold, similarityType, configurationId, disciplineId });
            
            // Сначала получаем все темы для функции
            const response = await fetch(`/api/similarities?labor_function_id=${functionId}&threshold=${threshold}&similarity_type=${similarityType}&configuration_id=${configurationId}`);
            log('Ответ от сервера:', response);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            log('Полученные темы по функции:', data);
            
            if (data.topics && Array.isArray(data.topics)) {
                // Если выбрана дисциплина, фильтруем темы
                if (disciplineId) {
                    // Получаем все темы для выбранной дисциплины
                    const topicsResponse = await fetch(`/api/topics?discipline_id=${disciplineId}`);
                    if (!topicsResponse.ok) {
                        throw new Error(`HTTP error! status: ${topicsResponse.status}`);
                    }
                    const disciplineTopics = await topicsResponse.json();
                    
                    // Создаем множество ID тем дисциплины для быстрого поиска
                    const disciplineTopicIds = new Set(disciplineTopics.map(t => t.id));
                    
                    // Фильтруем темы, оставляя только те, которые принадлежат выбранной дисциплине
                    const filteredTopics = data.topics.filter(topic => disciplineTopicIds.has(topic.id));
                    
                    updateTopicsTable(filteredTopics, true);
                } else {
                    // Если дисциплина не выбрана, показываем все темы
                    updateTopicsTable(data.topics, true);
                }
            } else {
                updateTopicsTable([]);
            }
        } catch (error) {
            log('Ошибка при загрузке тем по функции:', error);
            alert('Ошибка при загрузке тем по функции');
        }
    }

    // Обновляем функцию handleTopicClick
    function handleTopicClick(topicId) {
        log('Обработка клика по теме:', topicId);
        
        // Снимаем выделение с предыдущей выбранной темы
        if (selectedTopicId) {
            const prevRow = document.querySelector(`#topics-table tr[data-id="${selectedTopicId}"]`);
            if (prevRow) prevRow.classList.remove('selected');
        }
        
        // Выделяем новую тему
        const row = document.querySelector(`#topics-table tr[data-id="${topicId}"]`);
        if (row) row.classList.add('selected');
        
        selectedTopicId = topicId;
        selectedFunctionId = null;
        
        // Загружаем сходство и рекомендации
        loadSimilarities(topicId);
        loadSimilarityComparison(topicId);
    }

    // Обновляем обработчик клика по строке темы в updateTopicsTable
    function updateTopicsTable(topics, showSimilarity = false) {
        log('Обновление таблицы тем:', topics);
        topicsTable.innerHTML = '';
        if (!topics || topics.length === 0) {
            const row = document.createElement('tr');
            row.innerHTML = `<td colspan="4" style="text-align:center; color:#888;">Нет подходящих тем</td>`;
            topicsTable.appendChild(row);
            return;
        }
        topics.forEach(topic => {
            const row = document.createElement('tr');
            row.dataset.id = topic.id;
            row.innerHTML = `
                <td style="min-width: 40px; max-width: 60px;">${topic.type === 'lecture' ? 'Л' : (topic.type === 'practical' ? 'П' : '')}</td>
                <td style="width: 100%; white-space: normal;">${topic.name}</td>
                <td style="min-width: 40px; max-width: 60px;">${topic.hours !== null && topic.hours !== undefined ? topic.hours : '-'}</td>
                <td style="min-width: 60px; max-width: 80px;">${selectedTopicId === topic.id ? '-' : (showSimilarity && typeof topic.similarity === 'number' ? topic.similarity.toFixed(2) : '-')}</td>
            `;
            if (selectedTopicId === topic.id) row.classList.add('selected');
            row.onclick = () => handleTopicClick(topic.id);
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

    // Обновляем функцию updateRecommendations
    function updateRecommendations(recommendations) {
        log('Обновление рекомендаций:', recommendations);
        recommendationsDiv.innerHTML = '';
        
        if (!recommendations || recommendations.length === 0) {
            const div = document.createElement('div');
            div.textContent = 'Нет рекомендаций по улучшению формулировок';
            div.classList.add('recommendation-info');
            recommendationsDiv.appendChild(div);
            return;
        }
        
        recommendations.forEach(rec => {
            const div = document.createElement('div');
            div.textContent = rec.message;
            div.classList.add(`recommendation-${rec.type}`);
            recommendationsDiv.appendChild(div);
        });
    }

    // Обработчик изменения дисциплины
    function handleDisciplineChange() {
        const disciplineId = disciplineSelect.value;
        log('Изменена дисциплина:', disciplineId);
        
        if (disciplineId) {
            // Если выбрана трудовая функция, обновляем список тем для этой функции
            if (selectedFunctionId) {
                loadTopicsByFunction(selectedFunctionId);
            } else {
                // Иначе загружаем все темы дисциплины
                loadTopics(disciplineId);
            }
        } else {
            // Если дисциплина не выбрана, очищаем таблицу тем
            updateTopicsTable([]);
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
});