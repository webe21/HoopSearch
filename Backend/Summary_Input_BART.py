from transformers import BartForConditionalGeneration, BartTokenizer
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory
from rouge import Rouge

# Inisialisasi Sastrawi StopWordRemover
factory = StopWordRemoverFactory()
stopword_remover = factory.create_stop_word_remover()

# Load BART model dan tokenizer
model_name = "../Training data/fine_tuned_BART"
bart_model = BartForConditionalGeneration.from_pretrained(model_name)
bart_tokenizer = BartTokenizer.from_pretrained(model_name)

def remove_stopwords(sentence):
    # Menghapus stopwords menggunakan Sastrawi
    return stopword_remover.remove(sentence)

def summarize_sentence(sentence):
    # Hilangkan stopword sebelum masuk ke model
    filtered_sentence = remove_stopwords(sentence)
    
    # Tokenisasi dan generasi ringkasan
    inputs = bart_tokenizer([filtered_sentence], max_length=512, return_tensors="pt", truncation=True)
    summary_ids = bart_model.generate(
        inputs["input_ids"], 
        max_length=100, 
        min_length=50, 
        num_beams=5,  # Mengurangi beam untuk stabilitas
        no_repeat_ngram_size=2,  # Mengurangi pengulangan n-gram
        early_stopping=True  # Menghentikan proses lebih awal jika diperlukan
    )
    summary = bart_tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    return summary

def evaluate_summarization(predicted_summary, reference_summary):
    rouge = Rouge()
    scores = rouge.get_scores(predicted_summary, reference_summary)
    return{
        "ROUGE-1": scores[0]['rouge-1']['f'],
        "ROUGE-2": scores[0]['rouge-2']['f'],
        "ROUGE-L": scores[0]['rouge-l']['f']
    }

