from pymongo import MongoClient

# Menghubungkan ke MongoDB
client = MongoClient("mongodb+srv://Webe2101:Webe2101!@iblsearch.ha5bv.mongodb.net/?retryWrites=true&w=majority&appName=IBLSearch")
db = client["news_database"]

# Koleksi asal dan koleksi tujuan
source_collection = db["match_details"]
target_collection = db["match_headers"]

# Memilih data dari koleksi asal
for document in source_collection.find():
    # Mengambil data yang diperlukan
    match_header = {
        "match_id": str(document["_id"]),
        "date": document["date"],
        "home_team": document["match"]["home_team"]["name"],
        "home_score": document["match"]["home_team"]["score"],
        "away_team": document["match"]["away_team"]["name"],
        "away_score": document["match"]["away_team"]["score"]
    }

    # Memasukkan data header pertandingan ke koleksi tujuan jika belum ada
    if target_collection.count_documents({"match_id": match_header["match_id"]}, limit=1) == 0:
        target_collection.insert_one(match_header)
        print(f"Data pertandingan {match_header['match_id']} berhasil ditambahkan.")
    else:
        print(f"Data pertandingan {match_header['match_id']} sudah ada, tidak ditambahkan lagi.")

print("Proses selesai. Data header pertandingan berhasil dipindahkan tanpa duplikasi.")
