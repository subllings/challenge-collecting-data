import requests
from bs4 import BeautifulSoup
from typing import List, Dict
from src.utils.logger import logger

class ImmowebHTMLScraper:
    """
    Scraper for Immoweb public HTML pages.
    """

    BASE_URL = "https://www.immoweb.be/en/search/house/for-sale"

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Referer": "https://www.immoweb.be/en",
        "DNT": "1",  # Do Not Track
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1"
    }


    def __init__(self, city_slug: str = "brussels", max_pages: int = 2):
        """
        Initialize the HTML scraper.

        Args:
            city_slug (str): City in the URL slug format (e.g. "brussels", "namur")
            max_pages (int): Number of pages to fetch
        """
        self.city_slug = city_slug
        self.max_pages = max_pages

    def fetch_all(self) -> List[Dict]:
        results = []
        for page in range(1, self.max_pages + 1):
            url = f"{self.BASE_URL}/{self.city_slug}?page={page}"
            logger.info(f"Fetching {url}")
            try:
                response = requests.get(url, headers=self.HEADERS, timeout=10)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "html.parser")
                cards = soup.select("[data-test-id='search-result']")

                for card in cards:
                    title = card.select_one("[data-test-id='search-result-title']")
                    price = card.select_one("[data-test-id='search-result-price']")
                    location = card.select_one("[data-test-id='search-result-location']")
                    results.append({
                        "title": title.text.strip() if title else None,
                        "price": price.text.strip() if price else None,
                        "location": location.text.strip() if location else None
                    })
            except Exception as e:
                logger.error(f"Failed to fetch page {page}: {e}")
        return results
