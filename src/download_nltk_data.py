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

if __name__ == "__main__":
    download_nltk_resources() 