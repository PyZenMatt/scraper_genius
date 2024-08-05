import unittest
from unittest.mock import patch, Mock
from scraper import get_song_lyrics, search_songs, is_artist_valid, fetch_lyrics

class TestLyricsScraper(unittest.TestCase):

    @patch('scraper.requests.get')
    def test_get_song_lyrics_success(self, mock_get):
        # Mock the API response
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            'response': {
                'song': {
                    'path': '/songs/12345'
                }
            }
        }
        mock_html = Mock()
        mock_html.text = '<div class="lyrics">Sample lyrics</div>'
        mock_get.return_value.text = mock_html.text
        
        # Call the function
        lyrics = get_song_lyrics('/songs/12345')
        
        # Assert the lyrics are fetched correctly
        self.assertEqual(lyrics, 'Sample lyrics')

    @patch('scraper.requests.get')
    def test_get_song_lyrics_not_found(self, mock_get):
        # Mock the API response for song not found
        mock_get.return_value.status_code = 404
        
        # Call the function
        lyrics = get_song_lyrics('/songs/unknown')
        
        # Assert the lyrics are not available
        self.assertEqual(lyrics, 'Lyrics not available')

    @patch('scraper.requests.get')
    def test_search_songs_success(self, mock_get):
        # Mock the API response for searching songs
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            'response': {
                'hits': [
                    {
                        'result': {
                            'primary_artist': {
                                'name': 'Test Artist',
                                'id': 123
                            },
                            'api_path': '/songs/1',
                            'title': 'Test Song'
                        }
                    }
                ],
                'songs': [  # Mocked songs data structure to match the expected one
                    {
                        'api_path': '/songs/1',
                        'title': 'Test Song'
                    }
                ],
                'next_page': None
            }
        }

        # Call the function
        songs = search_songs('Test Artist')
        
        # Assert songs are returned correctly
        self.assertEqual(songs, [('Test Artist', 'Test Song', '/songs/1')])

    @patch('scraper.requests.get')
    def test_search_songs_artist_not_found(self, mock_get):
        # Mock the API response for artist not found
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {'response': {'hits': []}}

        # Call the function
        songs = search_songs('Unknown Artist')
        
        # Assert no songs are returned
        self.assertEqual(songs, [])

    @patch('scraper.requests.get')
    def test_is_artist_valid_true(self, mock_get):
        # Mock the API response for valid artist
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            'response': {
                'hits': [
                    {'result': {'primary_artist': {'name': 'Test Artist'}}}
                ]
            }
        }

        # Call the function
        is_valid = is_artist_valid('Test Artist')
        
        # Assert artist is valid
        self.assertTrue(is_valid)

    @patch('scraper.requests.get')
    def test_is_artist_valid_false(self, mock_get):
        # Mock the API response for invalid artist
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {'response': {'hits': []}}

        # Call the function
        is_valid = is_artist_valid('Unknown Artist')
        
        # Assert artist is not valid
        self.assertFalse(is_valid)

    @patch('scraper.get_song_lyrics')
    def test_fetch_lyrics(self, mock_get_song_lyrics):
        # Mock the lyrics fetching
        mock_get_song_lyrics.return_value = 'Sample lyrics'
        
        # Call the function
        result = fetch_lyrics(('Test Artist', 'Test Song', '/songs/1'))
        
        # Assert the result is correct
        expected = {'artist': 'Test Artist', 'title': 'Test Song', 'lyrics': 'Sample lyrics'}
        self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main()
