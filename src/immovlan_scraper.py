#from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from urllib.parse import urljoin
from seleniumwire import webdriver

import pandas as pd
import time
import random
import os
import logging
import json

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

        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        seleniumwire_options = {
            'request_storage': 'memory',
            'verify_ssl': False,
        }

        return webdriver.Chrome(options=options, seleniumwire_options=seleniumwire_options)





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
                f.write(f"\n=== Page {page} ===\n➡️ Visiting: {full_url}\n")
               

                self.driver.get(full_url)
                self.handle_cookie_banner()
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_all_elements_located((By.XPATH, "//a[contains(@href, '/en/detail/')]"))
                )                 

                # Scroll jusqu'en bas de la page pour forcer le chargement
                last_height = self.driver.execute_script("return document.body.scrollHeight")
                while True:
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)
                    new_height = self.driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        break
                    last_height = new_height
                time.sleep(random.uniform(1.5, 2.5))

                # Extraire les liens visibles dans la page
                link_elements = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/en/detail/')]")
                property_links = set()

                for elem in link_elements:
                    try:
                        href = elem.get_attribute("href")
                        if href and "/en/detail/" in href:
                            property_links.add(href.split("?")[0].strip())  # nettoyage basique
                    except Exception:
                        continue

                if not property_links:
                    msg = f"⚠️ No property links found on page {page}."
                    logger.warning(msg)
                    f.write(msg + "\n")
                    continue

                logger.info(f"🔗 Found {len(property_links)} property links on page {page}")
                f.write(f"🔗 Found {len(property_links)} property links on page {page}\n")

                for i, full_link in enumerate(sorted(property_links), start=1):
                    if full_link not in self.property_urls:
                      self.property_urls.append(full_link)
                    logger.info(f"[{i:02d}] ✅ URL found: {full_link}")
                    print(f"[{i:02d}] ✅ URL found: {full_link}")
                    f.write(f"[{i:02d}] {full_link}\n")

                # Dump HTML snapshot
                html = self.driver.page_source
                debug_path = f"output/debug_links_page_{page}.html"
                with open(debug_path, "w", encoding="utf-8") as dbg:
                    dbg.write(html)
                logger.info(f"📝 Saved HTML snapshot to {debug_path}")

        # Analyse les requêtes XHR pour extraire des données utiles
        for request in self.driver.requests:
            if request.response and "application/json" in request.headers.get("accept", ""):
                try:
                    body = request.response.body.decode('utf-8', errors='ignore')
                    data = json.loads(body)

                    # Parcours des propriétés si elles sont dans une clé 'items', 'list', ou 'results'
                    for container in ['items', 'list', 'results']:
                        if container in data:
                            for item in data[container]:
                                url = item.get("detailUrl") or item.get("url")
                                if url and url.startswith("http"):
                                    clean_url = url.split("?")[0]
                                    if clean_url not in self.property_urls:
                                        self.property_urls.append(clean_url)
                                        logger.info(f"📥 URL from JSON: {clean_url}")
                except Exception as e:
                    logger.debug(f"[XHR] Ignored non-parsable JSON: {request.url} ({str(e)})")



    def close(self):
        self.driver.quit()

    def to_csv(self, filepath="output/immovlan_urls.csv"):
        if not self.property_urls:
            logger.warning("⚠️ No URLs to save.")
            return
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        pd.DataFrame(self.property_urls, columns=["url"]).to_csv(filepath, index=False)
        logger.info(f"✅ Saved {len(self.property_urls)} URLs to {filepath}")



