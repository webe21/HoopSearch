import time
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pymongo import MongoClient
import numpy as np
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException

# MongoDB connection
try:
    client = MongoClient("mongodb+srv://Webe2101:Webe2101!@iblsearch.ha5bv.mongodb.net/?retryWrites=true&w=majority&appName=IBLSearch")
    client.admin.command('ping')  # Test connection
    print("Connected to MongoDB!")
except Exception as e:
    print(f"MongoDB connection error: {e}")
    exit()

db = client['news_database']
collection = db['match_details']

# Function to check if match exists in MongoDB
def match_exists(date, home_team, away_team):
    return collection.find_one({"date": date, "match.home_team.name": home_team, "match.away_team.name": away_team}) is not None

# Function to scrape player stats from the provided URL
def scrape_player_stats(stats_page_url):
    options = Options()
    options.headless = True
    driver = webdriver.Chrome(options=options)
    
    driver.get(stats_page_url)
    
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'playerStatsTable__row'))
        )
    except TimeoutException:
        print("Timeout: Element not found within the given time")
        driver.quit()
        return []

    stats_soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()

    players_data = []
    for row in stats_soup.find_all('div', class_='playerStatsTable__row'):
        try:
            stats_cells = row.find_all('div', class_='playerStatsTable__cell')
            player = {
                'name': row.find('div', class_='playerStatsTable__participantNameCell').text.strip(),
                'minutes_played': stats_cells[4].text.strip(),
                'points': stats_cells[1].text.strip(),
                'assists': stats_cells[3].text.strip(),
                'offensive_rebounds': stats_cells[14].text.strip() if len(stats_cells) > 14 else '0',
                'defensive_rebounds': stats_cells[15].text.strip() if len(stats_cells) > 15 else '0',
                'rebounds': stats_cells[2].text.strip(),
                'blocks': stats_cells[19].text.strip() if len(stats_cells) > 19 else '0',
                'steals': stats_cells[17].text.strip() if len(stats_cells) > 17 else '0',
                'fouls': stats_cells[16].text.strip() if len(stats_cells) > 16 else '0',
                'turnovers': stats_cells[18].text.strip() if len(stats_cells) > 18 else '0',
                'fgm': stats_cells[5].text.strip() if len(stats_cells) > 5 else '0',
                'fga': stats_cells[6].text.strip() if len(stats_cells) > 6 else '0',
                '2pm': stats_cells[7].text.strip() if len(stats_cells) > 7 else '0',
                '2pa': stats_cells[8].text.strip() if len(stats_cells) > 8 else '0',
                '3pm': stats_cells[9].text.strip() if len(stats_cells) > 9 else '0',
                '3pa': stats_cells[10].text.strip() if len(stats_cells) > 10 else '0',
                'ftm': stats_cells[11].text.strip() if len(stats_cells) > 11 else '0',
                'fta': stats_cells[12].text.strip() if len(stats_cells) > 12 else '0',
                'plus_minus': stats_cells[13].text.strip() if len(stats_cells) > 13 else '0'
            }
            players_data.append(player)
        except (AttributeError, IndexError):
            continue
    return players_data

# Function to scrape match data and insert directly into MongoDB
def scrape_and_insert():
    options = Options()
    options.headless = True
    driver = webdriver.Chrome(options=options)
    
    url = "https://www.basketball24.com/indonesia/ibl/results/"
    driver.get(url)

    # Wait for initial page load
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'div.sportName.basketball'))
    )

    # Close cookie consent if present
    try:
        cookie_consent = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, 'onetrust-accept-btn-handler'))
        )
        cookie_consent.click()
        print("Closed cookie consent.")
    except Exception:
        print("No cookie consent found or it couldn't be closed.")

    # Click the 'Show more matches' button repeatedly until new data is loaded
    while True:
        try:
            # Scroll down to make the button visible
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            # Find the "Show more matches" button and click it using JavaScript
            show_more_button = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'a.event__more.event__more--static'))
            )
            driver.execute_script("arguments[0].click();", show_more_button)
            print("Clicked 'Show more matches' button.")
            time.sleep(5)  # Allow time for more matches to load

            # Check if the last date is before or on 10 May
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            last_match_date = soup.find_all('div', class_='event__time')[-1].text.strip()
            if "10.05" in last_match_date:
                print("Reached data from 10 May or earlier.")
                break

        except Exception as e:
            print(f"Error clicking 'Show more matches': {e}")
            break

    # Parse the page after loading more matches
    page_source = driver.page_source
    driver.quit()

    soup = BeautifulSoup(page_source, 'html.parser')
    matches_section = soup.find('div', class_='sportName basketball')

    if matches_section:
        for match in matches_section.find_all('div', class_='event__match'):
            try:
                match_time = match.find('div', class_='event__time').text.strip()
                home_team = match.find('div', class_='event__participant--home').text.strip()
                away_team = match.find('div', class_='event__participant--away').text.strip()

                # Check if the match already exists in the database
                if match_exists(match_time, home_team, away_team):
                    print(f"Match between {home_team} and {away_team} on {match_time} already exists in the database.")
                    continue

                match_details = {
                    'time': match_time,
                    'home_team': home_team,
                    'away_team': away_team,
                    'home_score': match.find('div', class_='event__score--home').text.strip(),
                    'away_score': match.find('div', class_='event__score--away').text.strip()
                }

                match_id = re.findall(r'match\/(.*?)\/', match.find('a', class_='eventRowLink')['href'])[0]
                home_stats_url = f"https://www.basketball24.com/match/{match_id}/#/match-summary/player-statistics/1"
                away_stats_url = f"https://www.basketball24.com/match/{match_id}/#/match-summary/player-statistics/2"

                # Scrape player stats
                match_details['home_team_stats'] = scrape_player_stats(home_stats_url)
                match_details['away_team_stats'] = scrape_player_stats(away_stats_url)

                # Convert numpy types to Python-native types
                def convert_numpy(data):
                    if isinstance(data, dict):
                        return {k: convert_numpy(v) for k, v in data.items()}
                    elif isinstance(data, list):
                        return [convert_numpy(i) for i in data]
                    elif isinstance(data, (np.float32, np.float64)):
                        return float(data)
                    elif isinstance(data, (np.int32, np.int64)):
                        return int(data)
                    return data

                match_data = {
                    "date": match_details['time'],
                    "match": {
                        "home_team": {"name": match_details['home_team'], "score": match_details['home_score'], "players": match_details['home_team_stats']},
                        "away_team": {"name": match_details['away_team'], "score": match_details['away_score'], "players": match_details['away_team_stats']}
                    }
                }
                match_data = convert_numpy(match_data)

                # Insert directly into MongoDB
                try:
                    result = collection.insert_one(match_data)
                    print(f"Inserted match on {match_details['time']} with _id: {result.inserted_id}")
                except Exception as e:
                    print(f"Error inserting data: {e}")

            except AttributeError:
                continue

    print("Data scraping and insertion complete!")

# Main function to execute the scraping and insertion process
if __name__ == "__main__":
    scrape_and_insert()
