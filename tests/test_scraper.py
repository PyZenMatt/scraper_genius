import unittest
from unittest.mock import patch, Mock
import sys
import os
import requests.exceptions

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.scraper import search_songs, get_song_lyrics, fetch_lyrics

class TestScraper(unittest.TestCase):
    
    @patch('src.scraper.requests.get')
    def test_search_songs_success(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'response': {
                'hits': [{
                    'result': {
                        'primary_artist': {'name': 'Test Artist', 'id': 123},
                        'title': 'Test Song',
                        'api_path': '/songs/1'
                    }
                }],
                'songs': [{
                    'title': 'Test Song',
                    'api_path': '/songs/1',
                    'primary_artist': {'name': 'Test Artist'}
                }],
                'next_page': None
            }
        }
        mock_get.return_value = mock_response

        songs = search_songs('Test Artist')
        self.assertGreater(len(songs), 0)

    @patch('src.scraper.requests.get')
    def test_search_songs_artist_not_found(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'response': {'hits': []}}
        mock_get.return_value = mock_response

        songs = search_songs('Invalid Artist')
        self.assertEqual(len(songs), 0)

    @patch('src.scraper.requests.get')
    def test_get_song_lyrics_success(self, mock_get):
        api_mock = Mock()
        api_mock.json.return_value = {
            'response': {'song': {'url': 'http://fake.url'}}
        }
        
        html_mock = Mock()
        html_mock.text = '''<div data-lyrics-container="true">Test lyrics line 1<br>Test lyrics line 2</div>'''
        
        mock_get.side_effect = [api_mock, html_mock]
        
        lyrics = get_song_lyrics('/fake-path')
        self.assertIn("Test lyrics line 1", lyrics)
        self.assertGreaterEqual(lyrics.count('\n'), 1)

    @patch('src.scraper.requests.get')
    def test_get_song_lyrics_failure(self, mock_get):
        mock_get.side_effect = requests.exceptions.RequestException("Error")
        lyrics = get_song_lyrics('/invalid-path')
        self.assertEqual(lyrics, "Errore recupero testi")

    def test_fetch_lyrics_structure(self):
        test_song = ('Artist', 'Title', '/path')
        result = fetch_lyrics(test_song)
        self.assertEqual(result['artist'], 'Artist')
        self.assertEqual(result['title'], 'Title')
        self.assertIn('lyrics', result)

if __name__ == '__main__':
    unittest.main()