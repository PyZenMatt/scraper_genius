# Lyrics Scraper

This project is a Python script for scraping song lyrics from the Genius website using the Genius API.

## Features

- Retrieve song lyrics by artist name
- Save lyrics to a CSV file
- Mocked tests for reliable testing without real API calls

## Installation

1. Clone this repository:
   git clone https://github.com/your-username/lyrics-scraper.git

    Navigate to the project directory:


cd lyrics-scraper

Install the required dependencies:


    pip install -r requirements.txt

Usage

To run the scraper, use the following command:



python scraper.py "Artist Name" output.csv

Tests
Overview

The project includes a suite of unit tests that verify the functionality of the scraper. These tests use unittest and unittest.mock to simulate API responses and test various scenarios, including successful retrieval of lyrics, handling of missing data, and error cases.
Running Tests

To run the tests, execute:

python -m unittest discover tests

Test Coverage

    test_get_song_lyrics_success: Verifies successful retrieval of lyrics.
    test_get_song_lyrics_no_lyrics_found: Ensures correct handling when no lyrics are found.
    test_search_songs_artist_found: Checks the retrieval of songs for a found artist.
    test_search_songs_artist_not_found: Tests behavior when the artist is not found.
    test_is_artist_valid_found: Confirms the existence check for an artist.
    test_is_artist_valid_not_found: Ensures correct handling for non-existent artists.
    test_fetch_lyrics_success: Verifies fetching of lyrics for a song.
    test_save_lyrics_to_csv: Checks the saving of lyrics to a CSV file.

License

This project is licensed under the MIT License - see the LICENSE file for details.
