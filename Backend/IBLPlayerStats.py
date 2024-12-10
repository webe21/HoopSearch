from pymongo import MongoClient

# Menghubungkan ke MongoDB dengan URI yang Anda sediakan
client = MongoClient("mongodb+srv://Webe2101:Webe2101!@iblsearch.ha5bv.mongodb.net/?retryWrites=true&w=majority&appName=IBLSearch")
db = client["news_database"]  # Nama database

# Koleksi asal dan koleksi tujuan
source_collection = db["match_details"]
target_collection = db["player_stats"]

# Memilih data dari koleksi asal
for document in source_collection.find():
    match_id = str(document["_id"])  # Mengambil ObjectId sebagai string
    
    # Mengambil nama tim dan daftar pemain dari tim kandang dan tandang
    home_team_name = document["match"]["home_team"]["name"]
    away_team_name = document["match"]["away_team"]["name"]
    home_team_players = document["match"]["home_team"]["players"]
    away_team_players = document["match"]["away_team"]["players"]
    
    # Menambahkan data dari pemain home_team ke koleksi tujuan sebagai dokumen terpisah jika belum ada
    for player in home_team_players:
        player_data = {
            "match_id": match_id,
            "team_name": home_team_name,
            "name": player["name"]
        }

        # Mengecek apakah data pemain sudah ada
        if target_collection.count_documents(player_data, limit=1) == 0:
            # Menambahkan statistik lainnya jika data belum ada
            player_data.update({
                "minutes_played": player["minutes_played"],
                "points": player["points"],
                "assists": player["assists"],
                "offensive_rebounds": player["offensive_rebounds"],
                "defensive_rebounds": player["defensive_rebounds"],
                "rebounds": player["rebounds"],
                "blocks": player["blocks"],
                "steals": player["steals"],
                "fouls": player["fouls"],
                "turnovers": player["turnovers"],
                "fgm": player["fgm"],
                "fga": player["fga"],
                "2pm": player["2pm"],
                "2pa": player["2pa"],
                "3pm": player["3pm"],
                "3pa": player["3pa"],
                "ftm": player["ftm"],
                "fta": player["fta"],
                "plus_minus": player["plus_minus"]
            })
            target_collection.insert_one(player_data)
        else:
            print(f"Data pemain {player['name']} dari tim {home_team_name} dengan match_id {match_id} sudah ada, tidak ditambahkan lagi.")

    # Menambahkan data dari pemain away_team ke koleksi tujuan sebagai dokumen terpisah jika belum ada
    for player in away_team_players:
        player_data = {
            "match_id": match_id,
            "team_name": away_team_name,
            "name": player["name"]
        }

        # Mengecek apakah data pemain sudah ada
        if target_collection.count_documents(player_data, limit=1) == 0:
            # Menambahkan statistik lainnya jika data belum ada
            player_data.update({
                "minutes_played": player["minutes_played"],
                "points": player["points"],
                "assists": player["assists"],
                "offensive_rebounds": player["offensive_rebounds"],
                "defensive_rebounds": player["defensive_rebounds"],
                "rebounds": player["rebounds"],
                "blocks": player["blocks"],
                "steals": player["steals"],
                "fouls": player["fouls"],
                "turnovers": player["turnovers"],
                "fgm": player["fgm"],
                "fga": player["fga"],
                "2pm": player["2pm"],
                "2pa": player["2pa"],
                "3pm": player["3pm"],
                "3pa": player["3pa"],
                "ftm": player["ftm"],
                "fta": player["fta"],
                "plus_minus": player["plus_minus"]
            })
            target_collection.insert_one(player_data)
        else:
            print(f"Data pemain {player['name']} dari tim {away_team_name} dengan match_id {match_id} sudah ada, tidak ditambahkan lagi.")

print("Proses selesai. Data baru berhasil ditambahkan tanpa duplikasi.")
