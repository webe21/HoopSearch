from pymongo import MongoClient
from transformers import BertForTokenClassification, BertTokenizerFast
import torch
import pandas as pd
from bson import ObjectId
from sklearn.metrics import precision_score, recall_score, f1_score

# Load model dan tokenizer yang sudah dilatih
themodel = "../Training data/fine_tuned_IndoBERT_NER"
model = BertForTokenClassification.from_pretrained(themodel)
tokenizer = BertTokenizerFast.from_pretrained(themodel)

# Daftar label yang digunakan saat pelatihan
label_list = ["O", "B-PER", "B-ORG", "B-LOC", "B-TIME"]

# Koneksi ke MongoDB
client = MongoClient("mongodb+srv://Webe2101:Webe2101!@iblsearch.ha5bv.mongodb.net/?retryWrites=true&w=majority&appName=IBLSearch")
db = client.news_database
stats = db.player_stats
match = db.match_headers
match_detail = db.match_details

# Fungsi untuk tagging kalimat menggunakan model NER
def tag_sentence(sentence):
    sentence = sentence.split()
    inputs = tokenizer(sentence, return_tensors="pt", is_split_into_words=True)
        
    with torch.no_grad():
        output = model(**inputs)
        predictions = torch.argmax(output.logits, dim=2)

    predicted_labels = []
    word_ids = inputs.word_ids()
    prev_word_id = None
    for word_id, prediction in zip(word_ids, predictions[0]):
        if word_id is not None and word_id != prev_word_id:
            predicted_labels.append(label_list[prediction.item()])
        prev_word_id = word_id

    tagged_output = list(zip(sentence, predicted_labels))

    # Penyesuaian tambahan
    adjusted_tagged_output = []
    for word, tag in tagged_output:
        if word.lower() in {"melawan", "vs", "bertemu"}:
            adjusted_tagged_output.append((word, "B-GAME"))
        elif word.lower() in {"statistik", "stats", "performa"}:
            adjusted_tagged_output.append((word, "B-DATA"))
        else:
            adjusted_tagged_output.append((word, tag))

    return adjusted_tagged_output

# Fungsi untuk mendapatkan statistik pemain

file_path = "../Training data/data training/Player_Data_with_Duplicates.xlsx"
df = pd.read_excel(file_path)

def abbreviate_name(search_name):
    """
    Searches for an abbreviated name that matches the search_name by handling cases
    where the search input might only partially match or be in a different format,
    including initials and abbreviated formats.
    
    Args:
        search_name (str): The search input.
    
    Returns:
        tuple: The matched abbreviated name and full name or (None, None) if not found.
    """
    search_name = search_name.lower()  # Lowercase for case-insensitive matching
    search_parts = search_name.split()  # Split the search name into individual words

    # Iterate through each row to find a matching full name containing all parts of the search
    for _, row in df.iterrows():
        full_name = row['Nama Pemain IBL'].lower()  # Convert full name to lowercase
        abbreviated_name = row['Abbreviated Name'].lower()
        
        # Check if each part in the search name can match any part in either the full or abbreviated name
        if all(any(part in full_name_part or part in abbreviated_name for full_name_part in full_name.split()) 
               for part in search_parts):
            return row['Abbreviated Name'], row['Nama Pemain IBL']  # Return both names if any part matches

    return None, None  # Return None if no match is found

# Adjusting the get_player_statistics function to handle the returned tuple
def get_player_statistics(player_name):
    abbrev_name, full_name = abbreviate_name(player_name)  # Get both abbreviated and full names
    
    if not abbrev_name:
        return {'message': f'Data for player "{player_name}" not found.'}

    # Search MongoDB with the matched abbreviated name
    player_stats = stats.find({"name": {"$regex": f".*{abbrev_name}.*", "$options": "i"}})
    
    # Variabel untuk menampung total statistik dan jumlah game
    total_stats = { "points": 0, "assists": 0, 
        "rebounds": 0, "blocks": 0, "steals": 0,
        "turnovers": 0, "fgm": 0, "fga": 0, 
        "2pm": 0, "2pa": 0, "3pm": 0, "3pa": 0, 
        "ftm": 0, "fta": 0
    }
    game_count = 0

    # Fungsi bantu untuk konversi aman ke integer
    def safe_int(value):
        try:
            return int(value)
        except ValueError:
            return 0

    # Loop melalui semua game untuk pemain tersebut
    for game in player_stats:
        total_stats["points"] += safe_int(game.get("points", 0))
        total_stats["assists"] += safe_int(game.get("assists", 0))
        total_stats["rebounds"] += safe_int(game.get("rebounds", 0))
        total_stats["blocks"] += safe_int(game.get("blocks", 0))
        total_stats["steals"] += safe_int(game.get("steals", 0))
        total_stats["turnovers"] += safe_int(game.get("turnovers", 0))
        total_stats["fgm"] += safe_int(game.get("fgm", 0))
        total_stats["fga"] += safe_int(game.get("fga", 0))
        total_stats["2pm"] += safe_int(game.get("2pm", 0))
        total_stats["2pa"] += safe_int(game.get("2pa", 0))
        total_stats["3pm"] += safe_int(game.get("3pm", 0))
        total_stats["3pa"] += safe_int(game.get("3pa", 0))
        total_stats["ftm"] += safe_int(game.get("ftm", 0))
        total_stats["fta"] += safe_int(game.get("fta", 0))
        game_count += 1

    # Hitung rata-rata per game jika game_count > 0
    if game_count > 0:
        avg_stats = {stat: round(total / game_count, 2) for stat, total in total_stats.items()} 
        avg_stats["total_points"] = total_stats["points"]  # Menyimpan total poin secara terpisah
        avg_stats["total_game"] = game_count
    else:
        avg_stats = None

    return avg_stats

# Function to search matches by team name
def get_search_matches_by_team(team_name):
    matches = match.find({"$or": [{"home_team": {"$regex": team_name, "$options": "i"}},
                                  {"away_team": {"$regex": team_name, "$options": "i"}}]})
    results = []
    results = []
    for match_doc in matches:
        match_info = {
            "date": match_doc.get("date"),
            "home_team": match_doc.get("home_team"),
            "home_score": match_doc.get("home_score"),
            "away_team": match_doc.get("away_team"),
            "away_score": match_doc.get("away_score"),
            "match_id": match_doc.get("match_id")
        }
        results.append(match_info)

    return results if results else "Data not found"

# Mengubah urutan dari terbaru ke terlama menjadi terlama ke terbaru
def get_search_matches_by_game(team1, team2):
    matches = match.find({
        "$or": [
            {
                "$and": [
                    {"home_team": {"$regex": f"^{team1}$", "$options": "i"}},
                    {"away_team": {"$regex": f"^{team2}$", "$options": "i"}}
                ]
            },
            {
                "$and": [
                    {"home_team": {"$regex": f"^{team2}$", "$options": "i"}},
                    {"away_team": {"$regex": f"^{team1}$", "$options": "i"}}
                ]
            }
        ]
    }).sort("date", 1)  # Mengubah -1 menjadi 1 untuk pengurutan dari yang paling awal

    results = []
    results = []
    for match_doc in matches:
        match_info = {
            "date": match_doc.get("date"),
            "home_team": match_doc.get("home_team"),
            "home_score": match_doc.get("home_score"),
            "away_team": match_doc.get("away_team"),
            "away_score": match_doc.get("away_score"),
            "match_id": match_doc.get("match_id")
        }
        results.append(match_info)

    return results if results else "Data not found"


from bson import ObjectId

# Function to retrieve detailed match data based on match_id
def get_match_details(match_id):
    # Convert the match_id into an ObjectId instance
    match_data = match_detail.find_one({"_id": ObjectId(match_id)})

    if not match_data:
        return {"message": "Match details not found."}

    # Helper function to get player data with default values
    def get_player_details(player):
        return {
            "name": player.get("name", "N/A"),
            "minutes_played": player.get("minutes_played", "N/A"),
            "points": player.get("points", "N/A"),
            "assists": player.get("assists", "N/A"),
            "offensive_rebounds": player.get("offensive_rebounds", "N/A"),
            "defensive_rebounds": player.get("defensive_rebounds", "N/A"),
            "rebounds": player.get("rebounds", "N/A"),
            "blocks": player.get("blocks", "N/A"),
            "steals": player.get("steals", "N/A"),
            "fouls": player.get("fouls", "N/A"),
            "turnovers": player.get("turnovers", "N/A"),
            "fgm": player.get("fgm", "N/A"),
            "fga": player.get("fga", "N/A"),
            "two_pm": player.get("2pm", "N/A"),
            "two_pa": player.get("2pa", "N/A"),
            "three_pm": player.get("3pm", "N/A"),
            "three_pa": player.get("3pa", "N/A"),
            "ftm": player.get("ftm", "N/A"),
            "fta": player.get("fta", "N/A"),
            "plus_minus": player.get("plus_minus", "N/A")
        }

    # Construct the match details dictionary
    match_details = {
        "date": match_data.get("date", "N/A"),
        "home_team": {
            "name": match_data["match"]["home_team"].get("name", "N/A"),
            "score": match_data["match"]["home_team"].get("score", "N/A"),
            "players": [get_player_details(player) for player in match_data["match"]["home_team"].get("players", [])]
        },
        "away_team": {
            "name": match_data["match"]["away_team"].get("name", "N/A"),
            "score": match_data["match"]["away_team"].get("score", "N/A"),
            "players": [get_player_details(player) for player in match_data["match"]["away_team"].get("players", [])]
        }
    }

    return match_details

# Modifikasi fungsi `process_text` untuk mendukung tag `B-GAME`
def process_text(input_text):
    tagged_data = tag_sentence(input_text)

    # Collect contiguous non-"O" tags and process them
    processed_entities = []
    current_entity = []
    current_tags = set()

    for word, tag in tagged_data:
        if tag != "O" and tag != "B-GAME" and tag != "B-DATA":
            current_entity.append(word)
            current_tags.add(tag)
        else:
            if current_entity:
                if "B-ORG" in current_tags:
                    processed_entities.append((" ".join(current_entity), "B-ORG"))
                else:
                    processed_entities.append((" ".join(current_entity), "B-PER"))
                current_entity = []
                current_tags = set()

    # Handle the last entity if the input ends without an "O"
    if current_entity:
        if "B-ORG" in current_tags:
            processed_entities.append((" ".join(current_entity), "B-ORG"))
        else:
            processed_entities.append((" ".join(current_entity), "B-PER"))

    # Separate player names and team names based on tags
    player_names = [entity for entity, tag in processed_entities if tag == "B-PER"]
    team_names = [entity for entity, tag in processed_entities if tag == "B-ORG"]

    # Fetch player statistics
    player_averages = {}
    if player_names:
        for player_name in player_names:
            avg_stats = get_player_statistics(player_name)
            player_averages[player_name] = avg_stats if avg_stats else "Data not found"
    else:
        player_averages = {'message': 'Tidak ada tag B-PER dalam teks.'}

    # Jika tag B-GAME ada, ambil dua tim pertama dan cari semua pertandingan mereka
    if "B-GAME" in [tag for _, tag in tagged_data] and len(team_names) >= 2:
        match_data = {'match': get_search_matches_by_game(team_names[0], team_names[1])}
    else:
        # Fetch match data for each team
        match_data = {}
        if team_names:
            for team_name in team_names:
                matches = get_search_matches_by_team(team_name)
                match_data[team_name] = matches if matches else "Data not found"
        else:
            match_data = {'message': 'Tidak ada tag B-ORG dalam teks.'}
    
    return {'player_averages': player_averages, 'match_data': match_data}

def evaluate_ner(predicted_entities, true_entities):
    y_true = [1 if entity in true_entities else 0 for entity in predicted_entities]
    y_pred = [1 if entity in true_entities else 0 for entity in predicted_entities]
    
    precision = precision_score(y_true, y_pred, average='weighted')
    recall = recall_score(y_true, y_pred, average='weighted')
    f1 = f1_score(y_true, y_pred, average='weighted')
    
    return {
        "Precision": precision,
        "Recall": recall,
        "F1-Score": f1
    }
    