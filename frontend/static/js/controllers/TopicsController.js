class TopicsController {
    constructor(topicModel, topicsView, selectionController, functionsController = null, functionsView = null) {
        this.topicModel = topicModel;
        this.topicsView = topicsView;
        this.selectionController = selectionController;
        this.functionsController = functionsController;
        this.functionsView = functionsView;

        // Подписываемся на изменения в модели
        this.topicModel.subscribe(this.handleTopicsChange.bind(this));

        // Подписываемся на события выбора темы
        this.topicsView.container.addEventListener('topicSelected', this.handleTopicSelect.bind(this));
        this.topicsView.container.addEventListener('topicDeselected', this.handleTopicDeselect.bind(this));
    }

    setFunctionsController(functionsController) {
        this.functionsController = functionsController;
    }
    setFunctionsView(functionsView) {
        this.functionsView = functionsView;
    }

    handleTopicsChange() {
        const topics = this.topicModel.getAllTopics();
        console.log('TopicsController: handleTopicsChange, render all topics');
        this.topicsView.render(topics, null);
    }

    async handleTopicSelect(event) {
        console.log('TopicsController: handleTopicSelect', event.detail);
        const { topicId, topicType } = event.detail;
        const topic = this.topicModel.getTopicByIdType(topicId, topicType);
        if (topic) {
            this.selectionController.selectTopic(topic);
            // После выбора темы отображаем только выбранную тему
            const topics = this.topicModel.getAllTopics();
            console.log('TopicsController: render only selected topic', topic);
            this.topicsView.render(topics, topic);
        }
    }

    handleTopicDeselect() {
        console.log('TopicsController: handleTopicDeselect');
        this.selectionController.clearSelection();
        // После снятия выбора отображаем все темы
        const topics = this.topicModel.getAllTopics();
        console.log('TopicsController: render all topics (deselect)');
        this.topicsView.render(topics, null);
        // После снятия выбора темы отображаем все функции без сходства
        console.log('TopicsController: render all functions (deselect)');
        const functions = this.functionsController.getAllFunctions();
        this.functionsView.render(functions); // только список, без сходства
    }

    async loadTopics(disciplineId) {
        try {
            await this.topicModel.loadTopics(disciplineId);
        } catch (error) {
            console.error('Ошибка при загрузке тем:', error);
            throw error;
        }
    }

    getAllTopics() {
        return this.topicModel.getAllTopics();
    }

    filterTopics(predicate) {
        return this.topicModel.filterTopics(predicate);
    }

    updateRecommendations(recommendations) {
        const recommendationsDiv = document.getElementById('recommendations');
        if (!recommendationsDiv) return;

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
}

export default TopicsController; 