class FunctionsView {
    constructor(container) {
        this.container = container;
        this.selectedFunctionId = null;
        this.highSimilarityFunctions = new Set();
    }

    // Отрисовка карточки функции
    createFunctionCard(func) {
        const card = document.createElement('div');
        card.className = `function-card ${this.selectedFunctionId === func.id ? 'selected' : ''} ${this.highSimilarityFunctions.has(func.id) ? 'high-similarity' : ''}`;
        card.dataset.id = func.id;

        card.innerHTML = `
            <div class="function-name">${func.name}</div>
            ${func.similarity ? `<span class="similarity-indicator">${func.similarity.toFixed(2)}</span>` : ''}
        `;

        return card;
    }

    // Отрисовка всех функций
    render(functions, similarities = null) {
        if (similarities && similarities.functions) {
            // Создаем Map для быстрого доступа к сходству
            const similarityMap = new Map(
                similarities.functions.map(f => [f.id, f.similarity])
            );

            // Сортируем функции по сходству
            functions.sort((a, b) => {
                const aSimilarity = similarityMap.get(a.id) || 0;
                const bSimilarity = similarityMap.get(b.id) || 0;
                return bSimilarity - aSimilarity;
            });

            // Обновляем множество функций с высоким сходством (только топ-3)
            this.highSimilarityFunctions = new Set(
                similarities.functions
                    .sort((a, b) => b.similarity - a.similarity)
                    .slice(0, 3)
                    .map(f => f.id)
            );
        }

        // Создаем сетку карточек
        const grid = document.createElement('div');
        grid.className = 'functions-grid';

        // Добавляем карточки
        functions.forEach(func => {
            const card = this.createFunctionCard(func);
            grid.appendChild(card);
        });

        // Очищаем контейнер и добавляем сетку
        this.container.innerHTML = '';
        this.container.appendChild(grid);
        this.bindEvents();
    }

    // Установка выбранной функции
    setSelectedFunction(functionId) {
        this.selectedFunctionId = functionId;
        this.updateSelection();
    }

    // Обновление выделения
    updateSelection() {
        const cards = this.container.querySelectorAll('.function-card');
        cards.forEach(card => {
            card.classList.toggle('selected', card.dataset.id === this.selectedFunctionId);
        });
    }

    // Привязка обработчиков событий
    bindEvents() {
        const cards = this.container.querySelectorAll('.function-card');
        cards.forEach(card => {
            card.addEventListener('click', () => {
                const functionId = parseInt(card.dataset.id);
                this.setSelectedFunction(functionId);
                // Вызываем событие выбора функции
                const event = new CustomEvent('functionSelected', {
                    detail: { functionId }
                });
                this.container.dispatchEvent(event);
            });
        });
    }
}

export default FunctionsView; 