import nltk

def download_nltk_resources():
    """Загрузка необходимых ресурсов NLTK"""
    resources = [
        'punkt',
        'stopwords',
        'averaged_perceptron_tagger',
        'averaged_perceptron_tagger_ru',
        'punkt_tab'
    ]
    
    for resource in resources:
        print(f"Загрузка {resource}...")
        try:
            nltk.download(resource)
        except Exception as e:
            print(f"Ошибка при загрузке {resource}: {e}")
        else:
            print(f"{resource} успешно загружен")

def setup_nltk():
    """Загрузка необходимых данных NLTK"""
    try:
        nltk.data.find('tokenizers/punkt')
        nltk.data.find('corpora/stopwords')
    except LookupError:
        print("Загрузка необходимых данных NLTK...")
        nltk.download('punkt')
        nltk.download('stopwords')
        print("Загрузка завершена.")

if __name__ == "__main__":
    download_nltk_resources() 