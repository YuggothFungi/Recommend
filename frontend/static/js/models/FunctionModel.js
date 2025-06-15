class FunctionModel {
    constructor() {
        this.functions = [];
        this.listeners = new Set();
    }

    // Подписка на изменения
    subscribe(listener) {
        this.listeners.add(listener);
        return () => this.listeners.delete(listener);
    }

    // Уведомление подписчиков
    notify() {
        this.listeners.forEach(listener => listener(this.functions));
    }

    // Загрузка всех трудовых функций
    async loadFunctions() {
        try {
            const response = await fetch('/api/labor-functions');
            if (!response.ok) {
                throw new Error('Ошибка при загрузке трудовых функций');
            }
            const data = await response.json();
            this.functions = data;
            this.notify();
            return data;
        } catch (error) {
            console.error('Ошибка при загрузке трудовых функций:', error);
            throw error;
        }
    }

    // Получение функции по ID
    getFunctionById(id) {
        return this.functions.find(func => func.id === id);
    }

    // Получение всех функций
    getAllFunctions() {
        return [...this.functions];
    }

    // Фильтрация функций
    filterFunctions(predicate) {
        return this.functions.filter(predicate);
    }
}

export default FunctionModel; 