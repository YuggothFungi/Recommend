class SimilarityModel {
    constructor() {
        this.state = {
            threshold: 0.5,
            similarityType: 'rubert',
            configurationId: null
        };
        
        this.cache = {
            topicSimilarities: new Map(),
            functionSimilarities: new Map(),
            comparisons: new Map()
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

    // Установка порога
    setThreshold(value) {
        this.state.threshold = value;
        this.clearCache();
        this.notify();
    }

    // Установка типа сходства
    setSimilarityType(type) {
        this.state.similarityType = type;
        this.clearCache();
        this.notify();
    }

    // Установка ID конфигурации
    setConfigurationId(id) {
        this.state.configurationId = id;
        this.clearCache();
        this.notify();
    }

    // Загрузка сходства для темы
    async loadTopicSimilarities(topicId, topicType) {
        if (!this.state.configurationId) {
            throw new Error('Не выбрана конфигурация');
        }

        const cacheKey = `${topicId}_${topicType}_${this.state.threshold}_${this.state.similarityType}_${this.state.configurationId}`;
        
        if (this.cache.topicSimilarities.has(cacheKey)) {
            return this.cache.topicSimilarities.get(cacheKey);
        }

        try {
            const params = new URLSearchParams({
                topic_id: topicId,
                topic_type: topicType,
                threshold: this.state.threshold,
                similarity_type: this.state.similarityType,
                configuration_id: this.state.configurationId
            });

            const response = await fetch(`/api/similarities?${params.toString()}`);
            if (!response.ok) {
                throw new Error('Ошибка при загрузке сходства тем');
            }
            const data = await response.json();
            this.cache.topicSimilarities.set(cacheKey, data);
            return data;
        } catch (error) {
            console.error('Ошибка при загрузке сходства тем:', error);
            throw error;
        }
    }

    // Загрузка сходства для функции
    async loadFunctionSimilarities(functionId) {
        if (!this.state.configurationId) {
            throw new Error('Не выбрана конфигурация');
        }

        const cacheKey = `${functionId}_${this.state.threshold}_${this.state.similarityType}_${this.state.configurationId}`;
        
        if (this.cache.functionSimilarities.has(cacheKey)) {
            return this.cache.functionSimilarities.get(cacheKey);
        }

        try {
            const params = new URLSearchParams({
                labor_function_id: functionId,
                threshold: this.state.threshold,
                similarity_type: this.state.similarityType,
                configuration_id: this.state.configurationId
            });

            const response = await fetch(`/api/similarities?${params.toString()}`);
            if (!response.ok) {
                throw new Error('Ошибка при загрузке сходства функций');
            }
            const data = await response.json();
            this.cache.functionSimilarities.set(cacheKey, data);
            return data;
        } catch (error) {
            console.error('Ошибка при загрузке сходства функций:', error);
            throw error;
        }
    }

    // Загрузка сравнения сходства
    async loadSimilarityComparison(topicId) {
        if (!this.state.configurationId) {
            throw new Error('Не выбрана конфигурация');
        }

        const cacheKey = `${topicId}_${this.state.threshold}_${this.state.similarityType}_${this.state.configurationId}`;
        
        if (this.cache.comparisons.has(cacheKey)) {
            return this.cache.comparisons.get(cacheKey);
        }

        try {
            const params = new URLSearchParams({
                topic_id: topicId,
                threshold: this.state.threshold,
                similarity_type: this.state.similarityType,
                configuration_id: this.state.configurationId
            });

            const response = await fetch(`/api/similarity-comparison?${params.toString()}`);
            if (!response.ok) {
                throw new Error('Ошибка при загрузке сравнения сходства');
            }
            const data = await response.json();
            this.cache.comparisons.set(cacheKey, data);
            return data;
        } catch (error) {
            console.error('Ошибка при загрузке сравнения сходства:', error);
            throw error;
        }
    }

    // Очистка кэша
    clearCache() {
        this.cache.topicSimilarities.clear();
        this.cache.functionSimilarities.clear();
        this.cache.comparisons.clear();
    }

    // Получение текущего состояния
    getState() {
        return { ...this.state };
    }

    getConfigurationId() {
        return this.state.configurationId;
    }

    // Получение похожих функций для темы
    async getSimilarFunctions(topicId, topicType) {
        try {
            const data = await this.loadTopicSimilarities(topicId, topicType);
            return data.functions || [];
        } catch (error) {
            console.error('Ошибка при получении похожих функций:', error);
            return [];
        }
    }

    // Получение похожих тем для функции
    async getSimilarTopics(functionId) {
        try {
            const data = await this.loadFunctionSimilarities(functionId);
            return data.topics || [];
        } catch (error) {
            console.error('Ошибка при получении похожих тем:', error);
            return [];
        }
    }
}

export default SimilarityModel; 