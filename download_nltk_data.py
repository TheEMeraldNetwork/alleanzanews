import nltk

def download_nltk_data():
    print("Downloading required NLTK data...")
    nltk.download('punkt')
    nltk.download('averaged_perceptron_tagger')
    nltk.download('wordnet')
    nltk.download('brown')
    nltk.download('conll2000')
    nltk.download('maxent_ne_chunker')
    nltk.download('words')
    print("NLTK data downloaded successfully!")

if __name__ == "__main__":
    download_nltk_data() 