from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from urllib.parse import urljoin

import pandas as pd
import time
import random
import os
import logging

logger = logging.getLogger(__name__)

class ImmovlanScraper:
    def __init__(self, base_url: str, max_pages: int = 10, delay_min: float = 1.0, delay_max: float = 2.5):
        self.base_url = base_url
        self.max_pages = max_pages
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.driver = self._init_driver()
        self.property_urls = []
        self.data = []

    def _init_driver(self):
        options = Options()
        #options.add_argument("--headless")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        return webdriver.Chrome(options=options)



    def handle_cookie_banner(self):
        """
        Attempt to dismiss the cookie consent banner by clicking the 'Agree and close' button.
        """
        try:
            self.driver.switch_to.default_content()  # Ensure we're in the main context

            # Try clicking the cookie banner button by ID
            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "didomi-notice-agree-button"))
            ).click()

            logger.info("✅ Cookie consent dismissed successfully.")
        except Exception as e:
            logger.warning(f"⚠️ Cookie banner not found or could not be dismissed: {e}")


    def get_all_listing_urls(self):
        output_path = "output/immovlan_urls_by_page.log"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            for page in range(1, self.max_pages + 1):
                full_url = f"{self.base_url}&page={page}"
                logger.info(f"➡️ Visiting page {page}: {full_url}")
                f.write(f"\n=== Page {page} ===\n")
                f.write(f"➡️ Visiting: {full_url}\n")

                self.driver.get(full_url)
                self.handle_cookie_banner()

                delay = random.uniform(self.delay_min, self.delay_max)
                logger.info(f"⏳ Waiting {delay:.2f} seconds for JS to load...")
                time.sleep(delay)

                html = self.driver.page_source
                soup = BeautifulSoup(html, "html.parser")

                # 🔍 Dump html page
                debug_filename = f"output/debug_links_page_{page}.html"
                with open(debug_filename, "w", encoding="utf-8") as dbg:
                    dbg.write(soup.prettify())
                logger.info(f"📝 Saved HTML snapshot to {debug_filename}")

                # Sélectionne uniquement les liens valides vers des détails
                raw_links = soup.select("a[href^='https://immovlan.be/en/detail/']")
                if not raw_links:
                    msg = f"⚠️ No property links found on page {page}."
                    logger.warning(msg)
                    f.write(msg + "\n")
                    continue

                logger.info(f"🔗 Found {len(raw_links)} property links on page {page}")
                f.write(f"🔗 Found {len(raw_links)} property links on page {page}\n")

                seen_links = set()
                for i, card in enumerate(raw_links, start=1):
                    href = card.get("href")
                    if href:
                        full_link = urljoin("https://www.immovlan.be", href)
                        if full_link not in seen_links:
                            seen_links.add(full_link)
                            self.property_urls.append(full_link)

                            logger.info(f"[{i:02d}] ✅ URL found: {full_link}")
                            print(f"[{i:02d}] ✅ URL found: {full_link}")
                            f.write(f"[{i:02d}] {full_link}\n")

    def close(self):
        self.driver.quit()

    def to_csv(self, filepath="output/immovlan_urls.csv"):
        if not self.property_urls:
            logger.warning("⚠️ No URLs to save.")
            return
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        pd.DataFrame(self.property_urls, columns=["url"]).to_csv(filepath, index=False)
        logger.info(f"✅ Saved {len(self.property_urls)} URLs to {filepath}")