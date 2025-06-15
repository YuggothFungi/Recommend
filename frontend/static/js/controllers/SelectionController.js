class SelectionController {
    constructor(topicsView, functionsView, similarityModel) {
        this.topicsView = topicsView;
        this.functionsView = functionsView;
        this.similarityModel = similarityModel;
        this.selectedTopic = null;
        this.selectedFunction = null;
    }

    async selectTopic(topic) {
        console.log('SelectionController: selectTopic', topic);
        this.selectedTopic = topic;
        this.selectedFunction = null;
        this.functionsView.setSelectedFunction(null);
        try {
            const functions = await this.similarityModel.getSimilarFunctions(topic.id, topic.type);
            this.functionsView.render(functions);
        } catch (error) {
            console.error('Ошибка при загрузке функций:', error);
        }
    }

    async selectFunction(function_) {
        if (!this.selectedTopic) return;
        this.selectedFunction = function_;
        this.functionsView.setSelectedFunction(function_);
        try {
            const comparison = await this.similarityModel.getSimilarityComparison(
                this.selectedTopic.id,
                function_.id
            );
            this.functionsView.renderComparison(comparison);
        } catch (error) {
            console.error('Ошибка при загрузке сравнения:', error);
        }
    }

    clearSelection() {
        this.selectedTopic = null;
        this.selectedFunction = null;
        this.functionsView.setSelectedFunction(null);
    }

    getSelectedTopic() {
        return this.selectedTopic;
    }

    getSelectedFunction() {
        return this.selectedFunction;
    }

    async handleSelectionChange() {
        const state = this.selectionModel.getState();
        try {
            if (state.selectedTopic) {
                const similarities = await this.similarityModel.loadTopicSimilarities(state.selectedTopic.id);
                const functions = await this.similarityModel.getSimilarFunctions(state.selectedTopic.id);
                this.functionsView.render(functions, similarities);
                const comparison = await this.similarityModel.loadSimilarityComparison(state.selectedTopic.id);
                if (comparison && comparison.recommendations) {
                    this.updateRecommendations(comparison.recommendations);
                }
            } else if (state.selectedFunction) {
                const similarities = await this.similarityModel.loadFunctionSimilarities(state.selectedFunction.id);
                const topics = await this.similarityModel.getSimilarTopics(state.selectedFunction.id);
                this.topicsView.render(topics, similarities);
                const comparison = await this.similarityModel.loadSimilarityComparison(state.selectedFunction.id);
                if (comparison && comparison.recommendations) {
                    this.updateRecommendations(comparison.recommendations);
                }
            } else {
                this.topicsView.render([]);
                this.functionsView.render([]);
                this.updateRecommendations([]);
            }
        } catch (error) {
            console.error('Ошибка при загрузке сходства:', error);
        }
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

export default SelectionController; 