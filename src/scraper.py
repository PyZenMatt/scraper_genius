import requests
from bs4 import BeautifulSoup
import logging

GENIUS_ACCESS_TOKEN = ''

def search_songs(artist_name, stop_event=None, update_callback=None):
    base_url = "https://api.genius.com"
    headers = {'Authorization': f'Bearer {GENIUS_ACCESS_TOKEN}'}
    search_url = f"{base_url}/search"
    params = {'q': artist_name}

    try:
        response = requests.get(search_url, headers=headers, params=params)
        if response.status_code == 200:
            json_data = response.json()
            artist_id = None
            for hit in json_data['response']['hits']:
                if hit['result']['primary_artist']['name'].lower() == artist_name.lower():
                    artist_id = hit['result']['primary_artist']['id']
                    break

            if not artist_id:
                return []

            songs_url = f"{base_url}/artists/{artist_id}/songs"
            all_songs = []
            page = 1
            while True:
                if stop_event and stop_event.is_set():
                    return []
                params = {'page': page, 'per_page': 50}
                response = requests.get(songs_url, headers=headers, params=params)
                if response.status_code == 200:
                    songs_data = response.json()
                    if 'response' not in songs_data:
                        break
                    current_songs = [(artist_name, song['title'], song['api_path']) 
                                   for song in songs_data['response']['songs']]
                    all_songs.extend(current_songs)
                    
                    if update_callback:
                        update_callback([song[1] for song in current_songs])
                    
                    if not songs_data['response'].get('next_page'):
                        break
                    page += 1
                else:
                    break
            return all_songs
    except Exception as e:
        logging.error(f"Errore ricerca canzoni: {e}")
    return []

def get_song_lyrics(song_api_path, stop_event=None):
    if stop_event and stop_event.is_set():
        return "Operazione annullata"

    try:
        url = f"https://api.genius.com{song_api_path}"
        headers = {'Authorization': f'Bearer {GENIUS_ACCESS_TOKEN}'}
        response = requests.get(url, headers=headers)
        song_data = response.json()['response']['song']
        page_url = song_data['url']

        page = requests.get(page_url)
        soup = BeautifulSoup(page.text, 'html.parser')

        lyrics_div = soup.find('div', {'data-lyrics-container': 'true'})
        if lyrics_div:
            for br in lyrics_div.find_all('br'):
                br.replace_with('\n')
            return lyrics_div.get_text(separator='\n').strip()

        lyrics = soup.find('div', class_='lyrics') or \
                soup.find('div', class_='Lyrics__Container-sc-1ynbvzw-6') or \
                soup.find('div', class_='Lyrics__Root-sc-1ynbvzw-0')
        return lyrics.get_text(separator='\n').strip() if lyrics else "Testi non disponibili"

    except Exception as e:
        logging.error(f"Errore recupero testi: {e}")
        return "Errore recupero testi"

def fetch_lyrics(song):
    artist, title, path = song
    lyrics = get_song_lyrics(path)
    return {"artist": artist, "title": title, "lyrics": lyrics}