from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
from typing import List, Dict
import time
import logging

# Fallback logger if you don't use your custom logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class ImmowebPlaywrightScraperValidated:
    """
    Scraper using Playwright to interact with Immoweb JavaScript UI and extract listings.
    """

    def __init__(self, base_url: str, max_pages: int = 2, delay_between_requests: int = 3):
        self.base_url = base_url
        self.max_pages = max_pages
        self.delay = delay_between_requests

    def scrape_all_pages(self) -> List[Dict]:
        listings = []
        logger.info(f"Launching Playwright scraper for {self.max_pages} pages...")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            for page_num in range(1, self.max_pages + 1):
                url = f"{self.base_url}?countries=BE&page={page_num}&orderBy=relevance"
                logger.info(f"Scraping page {page_num}: {url}")

                try:
                    page.goto(url, timeout=60000)

                    # Try to click cookie banner if present
                    try:
                        page.locator("button:has-text('Accept')").click(timeout=5000)
                        logger.info("Accepted cookie banner.")
                    except PlaywrightTimeoutError:
                        logger.info("No cookie banner found or already accepted.")
                    except Exception as e:
                        logger.warning(f"Cookie click error: {e}")

                    # Wait before parsing
                    page.wait_for_timeout(self.delay * 1000)

                    html = page.content()
                    soup = BeautifulSoup(html, "html.parser")

                    listings_on_page = self.parse_listings(soup)
                    logger.info(f"{len(listings_on_page)} listings found on page {page_num}.")
                    listings.extend(listings_on_page)

                except Exception as e:
                    logger.error(f"Error scraping page {page_num}: {e}")

            browser.close()

        logger.info(f"Scraping completed. Total listings collected: {len(listings)}")
        return listings

    def parse_listings(self, soup: BeautifulSoup) -> List[Dict]:
        listings = []
        cards = soup.find_all("article", class_="card--result")

        for card in cards:
            try:
                title_tag = card.find("h2", class_="card__title")
                price_tag = card.find("span", class_="sr-only")
                location_tag = card.find("div", class_="card__information--property")

                title = title_tag.get_text(strip=True) if title_tag else None
                price = price_tag.get_text(strip=True) if price_tag else None
                location = location_tag.get_text(strip=True) if location_tag else None

                listings.append({
                    "title": title,
                    "price": price,
                    "location": location
                })
            except Exception as e:
                logger.warning(f"Skipping listing due to parsing error: {e}")

        return listings
