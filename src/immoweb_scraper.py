import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import time
import random
import pandas as pd
import logging


logger = logging.getLogger(__name__)

class ImmowebScraper:
    def __init__(self, base_url, max_pages=80, delay_min=1.5, delay_max=3.0):
        self.base_url = base_url
        self.max_pages = max_pages
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/115.0.0.0 Safari/537.36"
            )
        }
        self.property_urls = []
        self.data = []

    def get_base_urls(self):
        return [f"{self.base_url}?countries=BE&page={i}&orderBy=relevance" for i in range(1, self.max_pages + 1)]

    def fetch_property_links_playwright(self):
        all_links = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            for url in self.get_base_urls():
                logger.info(f"Fetching links (Playwright) from: {url}")
                try:
                    page.goto(url)
                    page.wait_for_selector("article.card--result", timeout=30000)

                    # Extraction claire via JS injecté
                    page_links = self._extract_property_urls_playwright(page)
                    all_links.extend(page_links)

                    delay = random.uniform(self.delay_min, self.delay_max)
                    logger.info(f"Sleeping for {delay:.2f}s to avoid blocking...")
                    time.sleep(delay)
                except Exception as e:
                    logger.error(f"Error fetching links (Playwright) from {url}: {e}")
            browser.close()
        self.property_urls = list(set(all_links))
        logger.info(f"Total unique property URLs collected (Playwright): {len(self.property_urls)}")
        return self.property_urls

    def fetch_property_details_playwright(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            for url in self.property_urls:
                logger.info(f"Scraping details (Playwright) from: {url}")
                try:
                    page.goto(url)

                    time.sleep(5)  # attente fixe pour debug

                    html = page.content()

                    print("=== Page HTML snapshot ===")
                    print(html[:1000])  # affiche un extrait du HTML

                    exists = page.evaluate("!!document.querySelector('article.card--result')")
                    print(f"Selector 'article.card--result' found? {exists}")

                    soup = BeautifulSoup(html, "html.parser")

                    title = soup.find("h1").get_text(strip=True) if soup.find("h1") else ""
                    price_tag = soup.find("p", class_="classified__price")
                    price = price_tag.get_text(strip=True) if price_tag else ""
                    locality_tag = soup.find("div", class_="classified__information--locality")
                    locality = locality_tag.get_text(strip=True) if locality_tag else ""

                    self.data.append({
                        "url": url,
                        "title": title,
                        "price": price,
                        "locality": locality
                    })

                    delay = random.uniform(self.delay_min, self.delay_max)
                    logger.info(f"Sleeping for {delay:.2f}s to avoid blocking...")
                    time.sleep(delay)
                except Exception as e:
                    logger.error(f"Failed to scrape (Playwright) {url}: {e}")
            browser.close()
        return self.data

    def _extract_property_urls_playwright(self, page) -> list[str]:
        """
        Extract all property URLs from the current Playwright page using JS evaluation.
        """
        urls = page.eval_on_selector_all(
            "article.card--result a.card__title-link",  # Sélecteur CSS exact
            "elements => elements.map(el => el.href).filter(href => href.includes('classified'))"
        )
        for url in urls:
            logger.info(f"Found property URL (Playwright): {url}")
        return urls

    def to_dataframe(self):
        return pd.DataFrame(self.data)

    def to_csv(self, filepath="data/output.csv"):
        df = self.to_dataframe()
        df.to_csv(filepath, index=False)
        logger.info(f"Data saved to {filepath}")



    def fetch_property_links_requests(self):
        all_links = []
        for url in self.get_base_urls():
            logger.info(f"Fetching links (requests) from: {url}")
            try:
                r = requests.get(url, headers=self.headers)
                r.raise_for_status()
                soup = BeautifulSoup(r.text, 'html.parser')

                links = [a['href'] for a in soup.select('article.card--result a.card__title-link') if a.has_attr('href')]
                all_links.extend(links)

                delay = random.uniform(self.delay_min, self.delay_max)
                logger.info(f"Sleeping for {delay:.2f}s to avoid blocking...")
                time.sleep(delay)
            except Exception as e:
                logger.error(f"Error fetching links (requests) from {url}: {e}")

        self.property_urls = list(set(all_links))
        logger.info(f"Total unique property URLs collected (requests): {len(self.property_urls)}")
        return self.property_urls