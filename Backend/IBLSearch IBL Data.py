import requests
from bs4 import BeautifulSoup
from transformers import pipeline, BartTokenizer
from pymongo import MongoClient

# Inisialisasi MongoDB
try:
    client = MongoClient("mongodb+srv://Webe2101:Webe2101!@iblsearch.ha5bv.mongodb.net/?retryWrites=true&w=majority&appName=IBLSearch")
    client.admin.command('ping')  # Test the connection
    print("Connected to MongoDB successfully!")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    exit()  # Exit if the connection fails

db = client['news_database']
collection = db['ibl_news']

# Inisialisasi tokenizer dan model summarizer
tokenizer_summarizer = BartTokenizer.from_pretrained("../Training data/fine_tuned_BART")
nlp_summarizer = pipeline("summarization", model="../Training data/fine_tuned_BART")

max_input_length = tokenizer_summarizer.model_max_length  # Panjang maksimal input untuk summarizer

# URL dasar untuk halaman berita IBL
base_url = "https://iblindonesia.com/news"

# Fungsi untuk mengambil data dari satu halaman
def fetch_news_page(page_num):
    url = f"{base_url}?per_page={page_num}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        print(f"Failed to retrieve page {page_num}")
        return None

# Fungsi untuk memproses konten HTML dan mengekstrak berita
def parse_news(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    articles = []  # Initialize list to store articles

    # Finding main articles with 'main-news-content'
    for article in soup.find_all('a', href=True):  
        main_content = article.find('div', class_='main-news-content')
        if main_content:
            try:
                # Mengambil title jika ada, jika tidak menggunakan "Unknown Title"
                title = main_content.find('h1').get_text(strip=True) if main_content.find('h1') else "Unknown Title"
                link = article['href']
                date = main_content.find('div', class_='date').get_text(strip=True) if main_content.find('div', class_='date') else "Unknown Date"
                
                # Memeriksa keberadaan artikel di database berdasarkan `link`
                if collection.find_one({"link": link}):
                    print(f"Article with link '{link}' already exists in the database. Skipping.")
                    continue  # Skip to the next article
                
                # Jika artikel baru, lanjutkan untuk merangkum dan menambahkan ke `articles`
                summary = fetch_and_summarize_article(link)
                articles.append({
                    "title": title,
                    "link": link,
                    "date": date,
                    "summary": summary
                })
            except AttributeError:
                continue  # Skip if any expected attribute is missing

    # Finding sub articles with 'sub-news-content'
    for article in soup.find_all('div', class_='sub-news-content'):
        try:
            # Mengambil title jika ada, jika tidak menggunakan "Unknown Title"
            title = article.find('h4', class_='sub-news-header').get_text(strip=True) if article.find('h4', class_='sub-news-header') else "Unknown Title"
            link = article.find('a')['href']
            date = article.find('div', class_='datesub').get_text(strip=True) if article.find('div', class_='datesub') else "Unknown Date"
            
            # Memeriksa keberadaan artikel di database berdasarkan `link`
            if collection.find_one({"link": link}):
                print(f"Article with link '{link}' already exists in the database. Skipping.")
                continue  # Skip to the next article

            # Jika artikel baru, lanjutkan untuk merangkum dan menambahkan ke `articles`
            summary = fetch_and_summarize_article(link)
            articles.append({
                "title": title,
                "link": link,
                "date": date,
                "summary": summary
            })
        except AttributeError:
            continue  # Skip if any expected attribute is missing

    print("Articles:", articles)

    return articles

def fetch_and_summarize_article(link):
    response = requests.get(link)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Mencari konten artikel di <div class="news-text">
    content_div = soup.find('div', class_='news-text')
    if content_div:
        full_text = " ".join(p.text for p in content_div.find_all('p'))  # Menggabungkan semua paragraf
        
        # Membatasi panjang teks jika melebihi batas maksimal summarizer
        if len(full_text) > max_input_length:
            full_text = full_text[:max_input_length]

        # Membuat ringkasan dari teks artikel
        summary = nlp_summarizer(full_text, max_length=130, min_length=30, do_sample=False)[0]['summary_text']
        return summary
    else:
        return "No content available"

# Fungsi utama untuk mengambil berita dari semua halaman dan menyimpannya ke MongoDB
def fetch_and_store_all_news():
    page = 1
    while True:
        print(f"Fetching page {page}...")
        html_content = fetch_news_page(page)
        if html_content:
            articles = parse_news(html_content)
            if articles:
                for article in articles:
                    collection.update_one({"link": article["link"]}, {"$set": article}, upsert=True)
            else:
                print(f"No new articles found on page {page}. Moving to the next page.")
            page += 1  # Tetap lanjut ke halaman berikutnya
        else:
            print("Failed to retrieve content, ending scraping.")
            break

# Menjalankan scraping dan penyimpanan
fetch_and_store_all_news()
