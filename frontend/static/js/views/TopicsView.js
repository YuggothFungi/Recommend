class TopicsView {
    constructor(container) {
        this.container = container;
    }

    render(topics, selectedTopic) {
        console.log('TopicsView: render', { topics, selectedTopic });
        const topicsToShow = selectedTopic
            ? topics.filter(
                t => String(t.id) === String(selectedTopic.id) && String(t.type) === String(selectedTopic.type)
            )
            : topics;

        this.container.innerHTML = '';
        const grid = document.createElement('div');
        grid.className = 'topics-grid';
        topicsToShow.forEach(topic => {
            const card = this.createTopicCard(topic, selectedTopic);
            grid.appendChild(card);
        });
        this.container.appendChild(grid);
    }

    createTopicCard(topic, selectedTopic) {
        const card = document.createElement('div');
        card.className = 'topic-card';
        card.setAttribute('data-topic-id', topic.id);
        card.setAttribute('data-topic-type', topic.type);
        if (
            selectedTopic &&
            String(topic.id) === String(selectedTopic.id) &&
            String(topic.type) === String(selectedTopic.type)
        ) {
            card.classList.add('selected');
        }

        const typeClass = topic.type === 'lecture' ? 'lecture' : 'practical';
        const typeText = topic.type === 'lecture' ? 'Л' : 'П';

        card.innerHTML = `
            <div class="topic-name">${topic.name}</div>
            <span class="topic-type ${typeClass}">${typeText}</span>
            ${topic.hours ? `<span class="topic-hours">${topic.hours}</span>` : ''}
            ${topic.similarity ? `<span class="similarity-indicator">${topic.similarity.toFixed(2)}</span>` : ''}
        `;

        // Добавляем кнопку закрытия, если тема выбрана
        if (
            selectedTopic &&
            String(topic.id) === String(selectedTopic.id) &&
            String(topic.type) === String(selectedTopic.type)
        ) {
            const closeButton = document.createElement('button');
            closeButton.className = 'close-button';
            closeButton.innerHTML = '&times;';
            closeButton.addEventListener('click', (e) => {
                e.stopPropagation();
                console.log('TopicsView: выбрасываем topicDeselected (closeButton)');
                this.container.dispatchEvent(new CustomEvent('topicDeselected', { bubbles: true }));
            });
            card.appendChild(closeButton);
        }

        card.addEventListener('click', (e) => {
            const clickedTopicId = card.getAttribute('data-topic-id');
            const clickedTopicType = card.getAttribute('data-topic-type');
            if (
                selectedTopic &&
                String(clickedTopicId) === String(selectedTopic.id) &&
                String(clickedTopicType) === String(selectedTopic.type)
            ) {
                // Повторный клик по выделенной теме — сброс выделения
                console.log('TopicsView: выбрасываем topicDeselected (card)');
                this.container.dispatchEvent(new CustomEvent('topicDeselected', { bubbles: true }));
            } else {
                console.log('TopicsView: выбрасываем topicSelected', { topicId: clickedTopicId, topicType: clickedTopicType });
                this.container.dispatchEvent(new CustomEvent('topicSelected', {
                    detail: { topicId: clickedTopicId, topicType: clickedTopicType },
                    bubbles: true
                }));
            }
        });

        return card;
    }
}

export default TopicsView; 