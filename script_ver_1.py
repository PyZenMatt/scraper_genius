import requests
from bs4 import BeautifulSoup
import pandas as pd
import logging
from concurrent.futures import ThreadPoolExecutor
import time

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Insert your Genius access token
GENIUS_ACCESS_TOKEN = 'Insert_token_here'

def get_song_lyrics(song_api_path):
    logging.info(f"Retrieving lyrics for {song_api_path}")
    url = f"https://api.genius.com{song_api_path}"
    headers = {'Authorization': f'Bearer {GENIUS_ACCESS_TOKEN}'}
    
    for _ in range(5):  # Retry up to 5 times
        try:
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                logging.error(f"Error retrieving song {song_api_path}: {response.status_code}")
                return "Lyrics not available"
            
            song_data = response.json()
            logging.info(f"Song data retrieved: {song_data}")
            path = song_data['response']['song']['path']
            
            page_url = f"https://genius.com{path}"
            logging.info(f"Retrieving HTML page from {page_url}")
            page = requests.get(page_url)
            html = BeautifulSoup(page.text, "html.parser")
            
            # Try different selectors for the lyrics
            lyrics = html.find("div", class_="lyrics")
            if lyrics is None:
                lyrics = html.find("div", class_="Lyrics__Container-sc-1ynbvzw-6 YYrds")
            if lyrics is None:
                lyrics = html.find("div", class_="Lyrics__Root-sc-1ynbvzw-0")
            if lyrics is None:
                logging.error(f"Lyrics not found for {song_api_path}")
                return "Lyrics not available"

            return lyrics.get_text(separator="\n").strip()
        
        except requests.exceptions.ConnectionError:
            logging.warning("Connection error. Retrying...")
            time.sleep(2)  # Wait 2 seconds before retrying
    return "Lyrics not available"

def search_songs(artist_name):
    base_url = "https://api.genius.com"
    headers = {'Authorization': f'Bearer {GENIUS_ACCESS_TOKEN}'}
    search_url = f"{base_url}/search"
    params = {'q': artist_name}
    logging.info(f"Searching for songs by {artist_name} on Genius")
    
    for _ in range(5):  # Retry up to 5 times
        try:
            response = requests.get(search_url, headers=headers, params=params)
            if response.status_code == 200:
                json_data = response.json()
                logging.info(f"JSON response received: {json_data}")
                artist_id = None
                for hit in json_data['response']['hits']:
                    if hit['result']['primary_artist']['name'].lower() == artist_name.lower():
                        artist_id = hit['result']['primary_artist']['id']
                        break
                
                if artist_id is None:
                    logging.error(f"Artist {artist_name} not found")
                    return []

                # Retrieve songs by the artist
                songs_url = f"{base_url}/artists/{artist_id}/songs"
                all_songs = []
                page = 1
                while True:
                    params = {'page': page, 'per_page': 50}  # Retrieve up to 50 songs per page
                    logging.info(f"Retrieving songs from page {page}")
                    response = requests.get(songs_url, headers=headers, params=params)
                    if response.status_code == 200:
                        songs_data = response.json()
                        logging.info(f"Songs found: {songs_data['response']['songs']}")
                        for song in songs_data['response']['songs']:
                            song_api_path = song['api_path']
                            title = song['title']
                            all_songs.append((artist_name, title, song_api_path))
                        if not songs_data['response']['next_page']:
                            break
                        page += 1
                    else:
                        logging.error(f"Error retrieving songs for {artist_name}: {response.status_code}")
                        break
                return all_songs
            else:
                logging.error(f"Error searching for songs by {artist_name}: {response.status_code}")
                time.sleep(2)  # Wait 2 seconds before retrying
        except requests.exceptions.ConnectionError:
            logging.warning("Connection error. Retrying...")
            time.sleep(2)  # Wait 2 seconds before retrying
    
    return []

def fetch_lyrics(song):
    artist, title, path = song
    lyrics = get_song_lyrics(path)
    return {"artist": artist, "title": title, "lyrics": lyrics}

def save_lyrics_to_csv(artist, filename="your_file.csv"):
    logging.info(f"Retrieving lyrics for {artist}")
    artist_songs = search_songs(artist)
    
    logging.info(f"Retrieving lyrics for {len(artist_songs)} songs")
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(fetch_lyrics, artist_songs)
    
    songs_data = list(results)
    df = pd.DataFrame(songs_data, columns=["artist", "title", "lyrics"])
    df.to_csv(filename, index=False)
    logging.info(f"Lyrics saved in {filename}")

if __name__ == "__main__":
    artist = "artist_name"
    save_lyrics_to_csv(artist)

