class TopicsController {
    constructor(topicModel, topicsView, selectionController) {
        this.topicModel = topicModel;
        this.topicsView = topicsView;
        this.selectionController = selectionController;

        // Подписываемся на изменения в модели
        this.topicModel.subscribe(this.handleTopicsChange.bind(this));

        // Подписываемся на события выбора темы
        this.topicsView.container.addEventListener('topicSelected', this.handleTopicSelect.bind(this));
        this.topicsView.container.addEventListener('topicDeselected', this.handleTopicDeselect.bind(this));
    }

    handleTopicsChange() {
        const topics = this.topicModel.getAllTopics();
        this.topicsView.render(topics, null);
    }

    async handleTopicSelect(event) {
        const { topicId, topicType } = event.detail;
        const topic = this.topicModel.getTopicById(topicId);
        if (topic) {
            this.selectionController.selectTopic(topic);
            // После выбора темы отображаем только выбранную тему
            const topics = this.topicModel.getAllTopics();
            this.topicsView.render(topics, topic);
        }
    }

    handleTopicDeselect() {
        this.selectionController.clearSelection();
        // После снятия выбора отображаем все темы
        const topics = this.topicModel.getAllTopics();
        this.topicsView.render(topics, null);
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