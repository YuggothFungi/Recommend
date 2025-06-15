class TopicModel {
    constructor() {
        this.topics = [];
        this.listeners = new Set();
    }

    // Подписка на изменения
    subscribe(listener) {
        this.listeners.add(listener);
        return () => this.listeners.delete(listener);
    }

    // Уведомление подписчиков
    notify() {
        this.listeners.forEach(listener => listener(this.topics));
    }

    // Загрузка тем по дисциплине
    async loadTopics(disciplineId) {
        try {
            const response = await fetch(`/api/topics?discipline_id=${disciplineId}`);
            if (!response.ok) {
                throw new Error('Ошибка при загрузке тем');
            }
            const data = await response.json();
            this.topics = data;
            this.notify();
            return data;
        } catch (error) {
            console.error('Ошибка при загрузке тем:', error);
            throw error;
        }
    }

    // Получение темы по ID и типу
    getTopicByIdType(id, type) {
        console.log('TopicModel: getTopicByIdType', id, type);
        return this.topics.find(topic => String(topic.id) === String(id) && String(topic.type) === String(type));
    }

    // Получение всех тем
    getAllTopics() {
        return [...this.topics];
    }

    // Фильтрация тем
    filterTopics(predicate) {
        return this.topics.filter(predicate);
    }
}

export default TopicModel; 