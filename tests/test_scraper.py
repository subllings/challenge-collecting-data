# Tests unitaires pour le scraper

import unittest
from src.scraper import fetch_html

class TestScraper(unittest.TestCase):
    def test_fetch_html(self):
        url = "https://example.com"
        html = fetch_html(url)
        self.assertTrue("Example Domain" in html)

if __name__ == "__main__":
    unittest.main()
