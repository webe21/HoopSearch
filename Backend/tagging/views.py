from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from transformers import BertForTokenClassification, BertTokenizerFast
import torch
import json
import re
from pymongo import MongoClient
from fuzzywuzzy import fuzz, process  # Import fuzzywuzzy untuk fuzzy matching
from Summary_Input_BART import summarize_sentence
from Tagging_Input_NER_IndoBert import tag_sentence, process_text, get_match_details

# Konfigurasi MongoDB Client
client = MongoClient("mongodb+srv://Webe2101:Webe2101!@iblsearch.ha5bv.mongodb.net/?retryWrites=true&w=majority&appName=IBLSearch")
db = client['news_database']  # Sesuaikan dengan nama database
collection = db['ibl_news']   # Sesuaikan dengan nama koleksi

themodel = "../Training data/fine_tuned_IndoBERT_NER"
model = BertForTokenClassification.from_pretrained(themodel)
tokenizer = BertTokenizerFast.from_pretrained(themodel)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = model.to(device)

# Fungsi preprocessing untuk membersihkan kalimat
def preprocess_text(text):
    text = text.lower()  # Konversi ke huruf kecil
    text = re.sub(r'[^\w\s]', '', text)  # Hapus tanda baca
    text = re.sub(r'\s+', ' ', text).strip()  # Hapus spasi berlebih
    return text

# Fungsi baru untuk saran konteks
def get_suggestion_with_context(word, titles):
    words_in_titles = set(sum([title.lower().split() for title in titles], []))
    best_match = process.extractOne(word, words_in_titles, scorer=fuzz.ratio)

    if best_match and best_match[1] > 80:
        return f"{preprocess_text(best_match[0])}"
    else:
        return word
    
    
def get_ner_embedding(text):
    """
    Menghasilkan embedding dari teks menggunakan model BERT yang telah di-finetune untuk NER.
    Mengambil rata-rata dari semua token atau menggunakan token [CLS] untuk representasi kalimat.
    """
    try:
        # Tokenisasi dengan truncation dan padding untuk memastikan dimensi konsisten
        inputs = tokenizer(
            text, 
            return_tensors="pt", 
            truncation=True, 
            padding=True, 
            max_length=512  # Sesuaikan dengan batas model BERT Anda
        ).to(device)
        
        # Pastikan perangkat model dan input sama (CPU atau GPU)
        with torch.no_grad():
            outputs = model(**inputs)
        
        # Ambil hidden state terakhir dari model
        last_hidden_state = outputs.last_hidden_state  # [batch_size, seq_len, hidden_dim]
        
        # Gunakan mean pooling (rata-rata semua token) untuk embedding
        embedding = last_hidden_state.mean(dim=1).squeeze().cpu().numpy()
        
        # Debugging untuk memeriksa dimensi embedding
        if embedding.ndim != 1:
            raise ValueError(f"Unexpected embedding shape: {embedding.shape}")

        return embedding
    except Exception as e:
        print(f"Error in get_ner_embedding: {str(e)}")

@csrf_exempt
def tag_query(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            sentence = data.get('sentence', '')

            if not sentence:
                return JsonResponse({"error": "No sentence provided"}, status=400)

            # Lakukan tagging NER pada kalimat asli
            tagged_output = tag_sentence(sentence)

            return JsonResponse({
                "original_sentence": sentence,
                "tagged_output": tagged_output,
            })

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=400)

@csrf_exempt
def find_similar_titles(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            sentence = data.get('sentence', "")

            if not sentence:
                return JsonResponse({"error": "No sentence provided"}, status=400)

            preprocessed_sentence = preprocess_text(sentence)

            # Ambil dokumen dari MongoDB
            documents = list(collection.find({}, {"title": 1, "link": 1, "summary": 1, "_id": 0}))
            titles = [doc['title'] for doc in documents]

            preprocessed_titles = [preprocess_text(title) for title in titles]

            # Hitung embedding
            #embeddings = [get_ner_embedding(preprocessed_sentence)] + [
                #get_ner_embedding(title) for title in preprocessed_titles
            #]

            # Validasi embedding
            #if not all(len(embedding.shape) == 1 for embedding in embeddings):
                #raise ValueError("Inconsistent embedding dimensions")

            #embedding_matrix = np.array(embeddings)
            
            vectorizer = TfidfVectorizer()
            vectors = vectorizer.fit_transform([preprocessed_sentence] + preprocessed_titles)
            cosine_similarities = cosine_similarity(vectors[0:1], vectors[1:]).flatten()

            # Hitung cosine similarity
            #cosine_similarities = cosine_similarity(embedding_matrix[0:1], embedding_matrix[1:]).flatten()

            similar_titles = [
                {
                    "title": documents[i]["title"],
                    "link": documents[i]["link"],
                    "summary": documents[i]["summary"],
                    "similarity_score": float(cosine_similarities[i]),
                }
                for i in range(len(documents))
            ]

            return JsonResponse({
                "original_sentence": sentence,
                "similar_titles": similar_titles
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Invalid request method"}, status=400)

@csrf_exempt
def player_statistics_view(request):
    if request.method == "POST":
        try:
            body = json.loads(request.body)
            input_text = body.get("text", "")

            if not input_text:
                return JsonResponse({"error": "Input text is required"}, status=400)
            
            # Process the text to get player statistics
            player_statistics = process_text(input_text)
            
            if player_statistics is None:
                return JsonResponse({"error": f"Data for player '{input_text}' not found."}, status=404)

            # Check if player_averages or specific error message exists
            if 'player_averages' in player_statistics:
                player_averages = player_statistics['player_averages']
                
                # Check if there's an error message in player_averages
                if isinstance(player_averages, dict):
                    for player, details in player_averages.items():
                        if isinstance(details, dict) and 'message' in details:
                            return JsonResponse({"error": details['message']}, status=404)
                
                # Return player averages data if no error message is found
                return JsonResponse({"player_averages": player_averages}, status=200)
            elif 'message' in player_statistics:
                return JsonResponse({"error": player_statistics['message']}, status=404)
            else:
                return JsonResponse({"error": "Data not found"}, status=404)
        
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=405)
    
@csrf_exempt
def match_statistics_view(request):
    if request.method == "POST":
        try:
            body = json.loads(request.body)
            input_text = body.get("text", "")

            if not input_text:
                return JsonResponse({"error": "Input text is required"}, status=400)
            
            # Process the text to get match statistics
            match_statistics = process_text(input_text)
            
            if match_statistics is None:
                return JsonResponse({"error": f"Data for match '{input_text}' not found."}, status=404)

            # Check if match_data exists and handle potential "Data not found" message
            if 'match_data' in match_statistics:
                match_data = match_statistics['match_data']
                
                # Check if match_data contains any "Data not found" message for a specific entry
                if isinstance(match_data, dict):
                    for key, value in match_data.items():
                        if value == "Data not found":
                            return JsonResponse({"error": f"Data for match '{key}' not found."}, status=404)
                
                # Return match data if no error message is found
                return JsonResponse({"match_data": match_data}, status=200)
            elif 'message' in match_statistics:
                return JsonResponse({"error": match_statistics['message']}, status=404)
            else:
                return JsonResponse({"error": "Data not found"}, status=404)
        
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=405)

@csrf_exempt
def match_details_view(request):
    if request.method == "POST":
        try:
            body = json.loads(request.body)
            match_id = body.get("match_id", "")

            if not match_id:
                return JsonResponse({"error": "Match ID is required"}, status=400)
            
            # Retrieve match details using match_id
            match_details = get_match_details(match_id)

            if match_details:
                return JsonResponse(match_details, status=200)
            else:
                return JsonResponse({"error": "Match details not found"}, status=404)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=405)
