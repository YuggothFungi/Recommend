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

        // Инициализация контроллеров
        this.selectionController = new SelectionController(
            this.topicsView,
            this.functionsView,
            this.similarityModel,
            this.topicModel
        );

        this.topicsController = new TopicsController(
            this.topicModel,
            this.topicsView,
            this.selectionController
        );

        this.functionsController = new FunctionsController(
            this.functionModel,
            this.functionsView,
            this.selectionController
        );

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

    handleConfigurationChange() {
        const configId = this.configurationSelect.value;
        if (configId) {
            this.similarityModel.setConfigurationId(configId);
        }
    }

    async handleDisciplineChange() {
        const disciplineId = this.disciplineSelect.value;
        if (disciplineId) {
            try {
                await this.topicsController.loadTopics(disciplineId);
            } catch (error) {
                console.error('Ошибка при загрузке тем:', error);
            }
        }
    }

    handleSimilarityTypeChange() {
        const type = this.similarityTypeSelect.value;
        this.similarityModel.setSimilarityType(type);
    }

    handleThresholdChange() {
        const value = this.thresholdSlider.value / 100;
        this.thresholdValue.textContent = value.toFixed(2);
        this.similarityModel.setThreshold(value);
    }
}

// Инициализация приложения при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    new App();
});