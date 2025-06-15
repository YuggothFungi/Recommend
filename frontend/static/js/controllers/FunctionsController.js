class FunctionsController {
    constructor(functionModel, functionsView, selectionController) {
        this.functionModel = functionModel;
        this.functionsView = functionsView;
        this.selectionController = selectionController;

        // Подписываемся на изменения в модели
        this.functionModel.subscribe(this.handleFunctionsChange.bind(this));

        // Подписываемся на события выбора функции
        this.functionsView.container.addEventListener('functionSelected', this.handleFunctionSelect.bind(this));
    }

    handleFunctionsChange() {
        const functions = this.functionModel.getAllFunctions();
        this.functionsView.render(functions);
    }

    async handleFunctionSelect(event) {
        const { functionId } = event.detail;
        const func = this.functionModel.getFunctionById(functionId);
        if (func) {
            // Уведомляем контроллер выбора
            this.selectionController.selectFunction(func);
        }
    }

    async loadFunctions() {
        try {
            await this.functionModel.loadFunctions();
        } catch (error) {
            console.error('Ошибка при загрузке функций:', error);
            throw error;
        }
    }

    getAllFunctions() {
        return this.functionModel.getAllFunctions();
    }

    filterFunctions(predicate) {
        return this.functionModel.filterFunctions(predicate);
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

export default FunctionsController; 