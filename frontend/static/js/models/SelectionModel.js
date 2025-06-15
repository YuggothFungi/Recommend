class SelectionModel {
    constructor() {
        this.state = {
            selectedTopic: null,
            selectedFunction: null
        };
        
        this.listeners = new Set();
    }

    // Подписка на изменения
    subscribe(listener) {
        this.listeners.add(listener);
        return () => this.listeners.delete(listener);
    }

    // Уведомление подписчиков
    notify() {
        this.listeners.forEach(listener => listener(this.state));
    }

    // Выбор темы
    selectTopic(topic) {
        this.state.selectedTopic = topic;
        this.state.selectedFunction = null;
        this.notify();
    }

    // Выбор функции
    selectFunction(function_) {
        this.state.selectedFunction = function_;
        this.state.selectedTopic = null;
        this.notify();
    }

    // Отмена выбора
    clearSelection() {
        this.state.selectedTopic = null;
        this.state.selectedFunction = null;
        this.notify();
    }

    // Получение текущего состояния
    getState() {
        return { ...this.state };
    }
}

export default SelectionModel; 