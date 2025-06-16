import SelectionModel from './models/SelectionModel.js';
import TopicModel from './models/TopicModel.js';
import FunctionModel from './models/FunctionModel.js';
import SimilarityModel from './models/SimilarityModel.js';

import TopicsView from './views/TopicsView.js';
import FunctionsView from './views/FunctionsView.js';

import SelectionController from './controllers/SelectionController.js';
import TopicsController from './controllers/TopicsController.js';
import FunctionsController from './controllers/FunctionsController.js';

class App {
    constructor() {
        // Инициализация моделей
        this.selectionModel = new SelectionModel();
        this.topicModel = new TopicModel();
        this.functionModel = new FunctionModel();
        this.similarityModel = new SimilarityModel();

        // Инициализация представлений
        this.topicsView = new TopicsView(document.getElementById('topics-container'));
        this.functionsView = new FunctionsView(document.getElementById('functions-container'));

        // Инициализация контроллеров (двусторонняя связь через сеттеры)
        this.selectionController = new SelectionController(
            this.topicsView,
            this.functionsView,
            this.similarityModel,
            this.topicModel
        );

        this.topicsController = new TopicsController(
            this.topicModel,
            this.topicsView,
            this.selectionController,
            null, // functionsController
            null  // functionsView
        );

        this.functionsController = new FunctionsController(
            this.functionModel,
            this.functionsView,
            this.selectionController,
            null, // topicsController
            null  // topicsView
        );

        // Устанавливаем двусторонние ссылки
        this.topicsController.setFunctionsController(this.functionsController);
        this.topicsController.setFunctionsView(this.functionsView);
        this.functionsController.setTopicsController(this.topicsController);
        this.functionsController.setTopicsView(this.topicsView);

        // Инициализация элементов управления
        this.initializeControls();
    }

    initializeControls() {
        // Элементы управления
        this.configurationSelect = document.getElementById('configuration-id');
        this.disciplineSelect = document.getElementById('discipline');
        this.similarityTypeSelect = document.getElementById('similarity-type');
        this.thresholdSlider = document.getElementById('threshold');
        this.thresholdValue = document.getElementById('threshold-value');

        // Привязка обработчиков событий
        this.configurationSelect.addEventListener('change', this.handleConfigurationChange.bind(this));
        this.disciplineSelect.addEventListener('change', this.handleDisciplineChange.bind(this));
        this.similarityTypeSelect.addEventListener('change', this.handleSimilarityTypeChange.bind(this));
        this.thresholdSlider.addEventListener('input', this.handleThresholdChange.bind(this));

        // Обработчик переключения вкладок
        const tabButtons = document.querySelectorAll('.tab-button');
        tabButtons.forEach(button => {
            button.addEventListener('click', async () => {
                // Убираем активный класс у всех кнопок и панелей
                document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
                document.querySelectorAll('.tab-pane').forEach(pane => pane.classList.remove('active'));
                
                // Добавляем активный класс выбранной кнопке и соответствующей панели
                button.classList.add('active');
                const tabId = button.getAttribute('data-tab');
                document.getElementById(tabId).classList.add('active');

                // Если выбрана вкладка "Изолированные элементы", загружаем данные
                if (tabId === 'isolated') {
                    await this.loadIsolatedElements();
                }
            });
        });

        // Загрузка начальных данных
        this.loadConfigurations();
        this.loadDisciplines();
        this.loadFunctions();
    }

    async loadConfigurations() {
        try {
            const response = await fetch('/api/configurations');
            if (!response.ok) {
                throw new Error('Ошибка при загрузке конфигураций');
            }
            const configs = await response.json();
            
            this.configurationSelect.innerHTML = `
                <option value="">Выберите конфигурацию</option>
                ${configs.map(config => `
                    <option value="${config.id}">${config.name}</option>
                `).join('')}
            `;
        } catch (error) {
            console.error('Ошибка при загрузке конфигураций:', error);
        }
    }

    async loadDisciplines() {
        try {
            const response = await fetch('/api/disciplines');
            if (!response.ok) {
                throw new Error('Ошибка при загрузке дисциплин');
            }
            const disciplines = await response.json();
            
            this.disciplineSelect.innerHTML = `
                <option value="">Выберите дисциплину</option>
                ${disciplines.map(discipline => `
                    <option value="${discipline.id}">${discipline.name}</option>
                `).join('')}
            `;
        } catch (error) {
            console.error('Ошибка при загрузке дисциплин:', error);
        }
    }

    async loadFunctions() {
        try {
            await this.functionsController.loadFunctions();
        } catch (error) {
            console.error('Ошибка при загрузке функций:', error);
        }
    }

    async handleConfigurationChange(event) {
        const configId = event.target.value;
        if (configId) {
            this.similarityModel.setConfigurationId(configId);
            // Если открыта вкладка с изолированными элементами, обновляем данные
            if (document.querySelector('.tab-button[data-tab="isolated"]').classList.contains('active')) {
                await this.loadIsolatedElements();
            }
        }
    }

    async handleDisciplineChange(event) {
        const disciplineId = event.target.value;
        if (disciplineId) {
            await this.topicModel.loadTopics(disciplineId);
            // Если открыта вкладка с изолированными элементами, обновляем данные
            if (document.querySelector('.tab-button[data-tab="isolated"]').classList.contains('active')) {
                await this.loadIsolatedElements();
            }
        }
    }

    async handleSimilarityTypeChange(event) {
        const type = event.target.value;
        this.similarityModel.setSimilarityType(type);
        // Если открыта вкладка с изолированными элементами, обновляем данные
        if (document.querySelector('.tab-button[data-tab="isolated"]').classList.contains('active')) {
            await this.loadIsolatedElements();
        }
    }

    async handleThresholdChange(event) {
        const value = event.target.value / 100;
        this.thresholdValue.textContent = value.toFixed(2);
        this.similarityModel.setThreshold(value);
        // Если открыта вкладка с изолированными элементами, обновляем данные
        if (document.querySelector('.tab-button[data-tab="isolated"]').classList.contains('active')) {
            await this.loadIsolatedElements();
        }
    }

    async loadIsolatedElements() {
        try {
            const configId = this.configurationSelect.value;
            const disciplineId = this.disciplineSelect.value;
            const similarityType = this.similarityTypeSelect.value;
            const threshold = this.thresholdSlider.value / 100;

            if (!configId) {
                console.warn('Не выбрана конфигурация для загрузки изолированных элементов');
                return;
            }

            const params = new URLSearchParams({
                configuration_id: configId,
                similarity_type: similarityType,
                threshold: threshold
            });

            if (disciplineId) {
                params.append('discipline_id', disciplineId);
            }

            const response = await fetch(`/api/isolated-elements?${params.toString()}`);
            if (!response.ok) {
                throw new Error('Ошибка при загрузке изолированных элементов');
            }

            const data = await response.json();
            this.updateIsolatedElements(data);
        } catch (error) {
            console.error('Ошибка при загрузке изолированных элементов:', error);
        }
    }

    updateIsolatedElements(data) {
        const topicsContainer = document.getElementById('isolated-topics');
        const functionsContainer = document.getElementById('isolated-functions');

        // Обновляем список изолированных тем
        topicsContainer.innerHTML = '';
        if (data.topics && data.topics.length > 0) {
            data.topics.forEach(topic => {
                const div = document.createElement('div');
                div.className = 'isolated-item';
                div.innerHTML = `
                    <span class="item-name">${topic.name}</span>
                    <span class="item-type">${topic.type === 'lecture' ? 'Л' : 'П'}</span>
                    <span class="item-similarity">${topic.max_similarity ? topic.max_similarity.toFixed(2) : 'Нет'}</span>
                `;
                topicsContainer.appendChild(div);
            });
        } else {
            topicsContainer.innerHTML = '<div class="no-items">Нет изолированных тем</div>';
        }

        // Обновляем список изолированных функций
        functionsContainer.innerHTML = '';
        if (data.functions && data.functions.length > 0) {
            data.functions.forEach(func => {
                const div = document.createElement('div');
                div.className = 'isolated-item';
                div.innerHTML = `
                    <span class="item-name">${func.name}</span>
                    <span class="item-similarity">${func.max_similarity ? func.max_similarity.toFixed(2) : 'Нет'}</span>
                `;
                functionsContainer.appendChild(div);
            });
        } else {
            functionsContainer.innerHTML = '<div class="no-items">Нет изолированных функций</div>';
        }
    }
}

// Инициализация приложения при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    new App();
});