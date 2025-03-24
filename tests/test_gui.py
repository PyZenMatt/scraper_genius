import unittest
from unittest.mock import patch, MagicMock
import tkinter as tk
import sys
import os
import queue
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.scraper import search_songs, fetch_lyrics
from src.gui import LyricsScraperApp, QueueHandler  

class TestLyricsScraperGUI(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.app = LyricsScraperApp()
        self.app.withdraw()
        
    def tearDown(self):
        self.app.destroy()
        self.root.destroy()

    def test_initial_state(self):
        """Test stato iniziale"""
        self.assertEqual(self.app.title(), "Genius Lyrics Scraper")

    @patch('src.gui.search_songs')
    def test_load_songs(self, mock_search):
        """Test caricamento canzoni"""
        test_songs = [('A','S1','/p1'), ('A','S2','/p2')]
        callback_calls = []
        
        def mock_impl(artist, stop_event, update_callback):
            if update_callback:
                callback_calls.append((artist, [s[1] for s in test_songs]))
            return test_songs
        
        mock_search.side_effect = mock_impl
        
        self.app.artist_entry.insert(0, "Test")
        self.app.load_button.invoke()
        
        mock_search.assert_called_once()
        self.assertEqual(len(callback_calls), 1)
        self.assertEqual(len(self.app.artist_songs), 2)

    @patch('src.gui.filedialog.asksaveasfilename')
    @patch('src.gui.fetch_lyrics')
    def test_download_lyrics(self, mock_fetch, mock_save):
        """Test download testi"""
        mock_save.return_value = "/fake/path.csv"
        mock_fetch.return_value = {"artist": "A", "title": "S1", "lyrics": "L1"}
        
        self.app.artist_songs = [('A', 'S1', '/p1')]
        self.app.songs_listbox.insert(tk.END, "S1")
        self.app.songs_listbox.selection_set(0)
        
        self.app.download_btn.invoke()
        self.assertTrue(mock_fetch.called)

    def test_log_handler(self):
        """Test sistema di logging"""
        test_queue = queue.Queue()
        handler = QueueHandler(test_queue)
        logger = logging.getLogger('test')
        logger.addHandler(handler)
        logger.error("Test error")
        self.assertFalse(test_queue.empty())

if __name__ == '__main__':
    unittest.main()