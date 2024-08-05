import requests
from bs4 import BeautifulSoup
import pandas as pd
import logging
from concurrent.futures import ThreadPoolExecutor
import time

# Configurazione del logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Inserisci il tuo token di accesso di Genius
GENIUS_ACCESS_TOKEN = 'Insert_token_here'

def get_song_lyrics(song_api_path):
    logging.info(f"Recupero del testo per {song_api_path}")
    url = f"https://api.genius.com{song_api_path}"
    headers = {'Authorization': f'Bearer {GENIUS_ACCESS_TOKEN}'}
    
    for _ in range(5):  # Retry fino a 5 volte
        try:
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                logging.error(f"Errore nel recupero del brano {song_api_path}: {response.status_code}")
                return "Testo non disponibile"
            
            song_data = response.json()
            logging.info(f"Dati del brano recuperati: {song_data}")
            path = song_data['response']['song']['path']
            
            page_url = f"https://genius.com{path}"
            logging.info(f"Recupero della pagina HTML da {page_url}")
            page = requests.get(page_url)
            html = BeautifulSoup(page.text, "html.parser")
            
            # Prova diversi selettori per i testi
            lyrics = html.find("div", class_="lyrics")
            if lyrics is None:
                lyrics = html.find("div", class_="Lyrics__Container-sc-1ynbvzw-6 YYrds")
            if lyrics is None:
                lyrics = html.find("div", class_="Lyrics__Root-sc-1ynbvzw-0")
            if lyrics is None:
                logging.error(f"Testo non trovato per {song_api_path}")
                return "Testo non disponibile"

            return lyrics.get_text(separator="\n").strip()
        
        except requests.exceptions.ConnectionError:
            logging.warning("Connection error. Retry...")
            time.sleep(2)  # Attendi 2 secondi prima di riprovare
    return "Testo non disponibile"

def search_songs(artist_name):
    base_url = "https://api.genius.com"
    headers = {'Authorization': f'Bearer {GENIUS_ACCESS_TOKEN}'}
    search_url = f"{base_url}/search"
    params = {'q': artist_name}
    logging.info(f"Ricerca dei brani per {artist_name} su Genius")
    
    for _ in range(5):  # Retry fino a 5 volte
        try:
            response = requests.get(search_url, headers=headers, params=params)
            if response.status_code == 200:
                json_data = response.json()
                logging.info(f"Risposta JSON ricevuta: {json_data}")
                artist_id = None
                for hit in json_data['response']['hits']:
                    if hit['result']['primary_artist']['name'].lower() == artist_name.lower():
                        artist_id = hit['result']['primary_artist']['id']
                        break
                
                if artist_id is None:
                    logging.error(f"Artista {artist_name} non trovato")
                    return []

                # Recupera canzoni dell'artista
                songs_url = f"{base_url}/artists/{artist_id}/songs"
                all_songs = []
                page = 1
                while True:
                    params = {'page': page, 'per_page': 50}  # Recupera fino a 50 canzoni per pagina
                    logging.info(f"Recupero delle canzoni dalla pagina {page}")
                    response = requests.get(songs_url, headers=headers, params=params)
                    if response.status_code == 200:
                        songs_data = response.json()
                        logging.info(f"Brani trovati: {songs_data['response']['songs']}")
                        for song in songs_data['response']['songs']:
                            song_api_path = song['api_path']
                            title = song['title']
                            all_songs.append((artist_name, title, song_api_path))
                        if not songs_data['response']['next_page']:
                            break
                        page += 1
                    else:
                        logging.error(f"Errore nel recupero dei brani per {artist_name}: {response.status_code}")
                        break
                return all_songs
            else:
                logging.error(f"Errore nella ricerca dei brani per {artist_name}: {response.status_code}")
                time.sleep(2)  # Attendi 2 secondi prima di riprovare
        except requests.exceptions.ConnectionError:
            logging.warning("Connection error. Retry...")
            time.sleep(2)  # Attendi 2 secondi prima di riprovare
    
    return []

def fetch_lyrics(song):
    artist, title, path = song
    lyrics = get_song_lyrics(path)
    return {"artista": artist, "titolo": title, "testo": lyrics}

def save_lyrics_to_csv(artist, filename="your_file.csv"):
    logging.info(f"Recupero dei testi per {artist}")
    artist_songs = search_songs(artist)
    
    logging.info(f"Recupero dei testi per {len(artist_songs)} brani")
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(fetch_lyrics, artist_songs)
    
    songs_data = list(results)
    df = pd.DataFrame(songs_data, columns=["artista", "titolo", "testo"])
    df.to_csv(filename, index=False)
    logging.info(f"Testi salvati in {filename}")

if __name__ == "__main__":
    artist = "artist_name"
    save_lyrics_to_csv(artist)
