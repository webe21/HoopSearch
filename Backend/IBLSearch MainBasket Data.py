import requests
from bs4 import BeautifulSoup
from transformers import pipeline, BartTokenizer
from pymongo import MongoClient

# MongoDB setup with connection test
try:
    client = MongoClient("mongodb+srv://Webe2101:Webe2101!@iblsearch.ha5bv.mongodb.net/?retryWrites=true&w=majority&appName=IBLSearch")
    client.admin.command('ping')  # Test the connection
    print("Connected to MongoDB successfully!")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    exit()  # Exit if the connection fails

db = client['news_database']
collection = db['ibl_news']

base_url = "https://www.mainbasket.com/c/5/berita/ibl?page={}"

# Load tokenizer and model for summarization
tokenizer_summarizer = BartTokenizer.from_pretrained("../Training data/fine_tuned_BART")
nlp_summarizer = pipeline("summarization", model="../Training data/fine_tuned_BART")

max_input_length = tokenizer_summarizer.model_max_length

page = 1
while True:
    url = base_url.format(page)
    print(f"Scraping URL: {url}")
    
    # Request the page
    response = requests.get(url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        articles = soup.find_all('div', class_='post-title')
        print(f"Found {len(articles)} articles on page {page}")
        
        # If no articles are found, break the loop
        if not articles:
            print(f"No articles found on page {page}. Ending scraping.")
            break
        
        for article in articles:
            link = article.find('a')
            if link:
                title = link.get_text(strip=True)
                href = link['href']
                full_link = href
                print(f"Processing article: {title}")
                
                # Check if the title already exists in the database
                existing_article = collection.find_one({"title": title})
                if collection.find_one({"title": title}):
                    print(f"Article '{title}' already exists in the database. Skipping...")
                    continue  # Skip if already in the database
                
                # Scrape article content
                article_response = requests.get(full_link)
                if article_response.status_code == 200:
                    article_soup = BeautifulSoup(article_response.content, 'html.parser')
                    
                    # Extract the main content from the 'post-body' div
                    post_body = article_soup.find('div', class_='post-body')
                    if post_body:
                        content_divs = post_body.find_all('p')  # Find all <p> tags in the post-body
                        content = " ".join([p.get_text(strip=True) for p in content_divs if p.get_text(strip=True)])  # Concatenate all the text
                        
                        if content:
                            print(f"Article content preview: {content[:100]}...")  # Print a preview of the content
                            
                            # If content is too long, truncate
                            if len(content) > max_input_length:
                                content = content[:max_input_length]
                            
                            # Summarize content
                            try:
                                summary = nlp_summarizer(content, max_length=100, min_length=50, do_sample=False)
                                if summary:
                                    article_summary = summary[0]['summary_text']
                                    print(f"Summary: {article_summary}")
                                else:
                                    article_summary = "Summary is empty."
                            except Exception as e:
                                article_summary = f"Error during summarization: {e}"
                            
                            # Insert into MongoDB
                            article_data = {
                                "title": title,
                                "link": full_link,
                                "summary": article_summary
                            }
                            try:
                                result = collection.insert_one(article_data)
                                print(f"Inserted article with _id: {result.inserted_id}")
                            except Exception as e:
                                print(f"Failed to insert document into MongoDB: {e}")
                        else:
                            print("Content is empty or not valid for summarization.")
                    else:
                        print("Post-body div not found.")
                else:
                    print(f"Failed to retrieve article at {full_link}. Status code: {article_response.status_code}")
    
    else:
        print(f"Failed to retrieve page {page}. Status code: {response.status_code}")
    
    # Move to the next page
    page += 1
