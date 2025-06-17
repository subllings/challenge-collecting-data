from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from seleniumwire import webdriver
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin

import pandas as pd
import time
import random
import os
import logging
import json

logger = logging.getLogger(__name__)

class ImmovlanScraper:
    def __init__(self, base_url: str, max_pages: int = 10, delay_min: float = 1.0, delay_max: float = 2.5, run_id: str = None):
        self.base_url = base_url
        self.max_pages = max_pages
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.run_id = run_id or datetime.now().strftime("%Y%m%d_%H%M")
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
        Try to dismiss cookie consent popup if present.
        """
        try:
            accept_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button, [id*='cookie'], [class*='cookie']"))
            )
            accept_button.click()
            logger.info("✅ Cookie banner dismissed.")
        except TimeoutException:
            logger.info("ℹ️ No cookie banner found.")
        except Exception as e:
            logger.warning(f"⚠️ Unexpected error while handling cookie banner: {e}")


    def get_all_listing_urls(self):
        output_path = f"output/immovlan_urls_by_page_{self.run_id}.log"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        empty_pages_in_a_row = 0
        max_empty_pages = 10
        same_pages_in_a_row = 0
        max_same_pages = 10
        last_page_links = []

        with open(output_path, "w", encoding="utf-8") as f:
            for page in range(1, self.max_pages + 1):
                full_url = f"{self.base_url}&page={page}"
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                logger.info(f">>> Visiting page {page}: {full_url}")
                f.write(f"\n[{timestamp}] === Page {page} ===\n>>> Visiting: {full_url}\n")

                self.driver.get(full_url)
                self.driver.requests.clear()  # ✅ Clear previous network traffic for this page
                self.handle_cookie_banner()

                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/en/detail/']"))
                    )
                except TimeoutException:
                    msg = f"[WARNING] Timeout on page {page}. Page structure not recognized. Skipping."
                    logger.warning(msg)
                    f.write(f"[{timestamp}] {msg}\n")
                    empty_pages_in_a_row += 1
                    if empty_pages_in_a_row >= max_empty_pages:
                        stop_msg = (
                            f"\n[{timestamp}] 🛑 Script stopped after {max_empty_pages} consecutive pages "
                            f"with no valid listings (last at page {page})."
                        )
                        logger.warning(stop_msg)
                        f.write(stop_msg + "\n")
                        break
                    continue

                # Scroll to force lazy loading
                last_height = self.driver.execute_script("return document.body.scrollHeight")
                while True:
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(random.uniform(1.5, 2.5))
                    new_height = self.driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        break
                    last_height = new_height

                # Extract links from the DOM
                links_dom = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/en/detail/')]")
                dom_links = {
                    elem.get_attribute("href").split("?")[0].strip()
                    for elem in links_dom
                    if elem.get_attribute("href") and "/en/detail/" in elem.get_attribute("href")
                }

                # Extract links from XHR JSON
                xhr_links = set()
                for req in self.driver.requests:
                    if req.response and "application/json" in req.headers.get("accept", ""):
                        try:
                            body = req.response.body.decode("utf-8", errors="ignore")
                            data = json.loads(body)
                            for container in ['items', 'list', 'results']:
                                if container in data:
                                    for item in data[container]:
                                        url = item.get("detailUrl") or item.get("url")
                                        if url and url.startswith("http"):
                                            xhr_links.add(url.split("?")[0])
                        except Exception:
                            continue

                page_links = sorted(dom_links.union(xhr_links))
                #  Stop if current page returns exactly same links as the previous one
                if page_links == last_page_links:
                    same_pages_in_a_row += 1
                    msg = f"[WARNING] Same links as previous page at page {page} ({same_pages_in_a_row} in a row)."
                    logger.warning(msg)
                    f.write(f"[{timestamp}] {msg}\n")

                    if same_pages_in_a_row >= max_same_pages:
                        stop_msg = (
                            f"\n[{timestamp}] 🛑 Stopping: {max_same_pages} pages with identical links detected. Likely the end."
                        )
                        logger.warning(stop_msg)
                        f.write(stop_msg + "\n")
                        break
                else:
                    same_pages_in_a_row = 0

                last_page_links = page_links                

                if not page_links:
                    msg = f"[WARNING] No property links found on page {page}."
                    logger.warning(msg)
                    f.write(f"[{timestamp}] {msg}\n")
                    empty_pages_in_a_row += 1
                    if empty_pages_in_a_row >= max_empty_pages:
                        stop_msg = (
                            f"\n[{timestamp}] 🛑 Script stopped after {max_empty_pages} consecutive empty pages "
                            f"(last at page {page})."
                        )
                        logger.warning(stop_msg)
                        f.write(stop_msg + "\n")
                        break
                    continue
                else:
                    empty_pages_in_a_row = 0

                logger.info(f"[INFO] Found {len(page_links)} property links on page {page}")
                f.write(f"[{timestamp}] [INFO] Found {len(page_links)} property links on page {page}\n")

                page_data = []  # store URLs from this page only

                for i, url in enumerate(page_links, 1):
                    entry = {"page": page, "url": url}
                    if entry not in self.property_urls:
                        self.property_urls.append(entry)
                    page_data.append(entry)
                    logger.info(f"🟢 [{i:02d}] URL found: {url}")
                    f.write(f"[{timestamp}] 🟢 [{i:02d}] {url}\n")

                # ✅ Save partial CSV with only this page’s URLs
                partial_csv_path = f"output/partial_urls_page_{page}_{self.run_id}.csv"
                pd.DataFrame(page_data, columns=["page", "url"]).to_csv(partial_csv_path, index=False)
                logger.info(f"[INFO] ✅ Partial CSV saved: {partial_csv_path}")

        # ✅ Final save of all collected URLs
        self.to_csv(filepath=f"output/immovlan_urls_{self.run_id}.csv")

        # Optional: Save summary stats
        summary_path = f"output/stats_{self.run_id}.txt"
        with open(summary_path, "w") as stats:
            stats.write(f"Run ID         : {self.run_id}\n")
            stats.write(f"Pages visited  : {page}\n")
            stats.write(f"Total listings : {len(self.property_urls)}\n")
            stats.write(f"Timestamp      : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        logger.info(f"📊 Stats saved to {summary_path}")




    def close(self):
        self.driver.quit()

    def to_csv(self, filepath: str):
        if not self.property_urls:
            logger.warning("[WARNING] No URLs to save.")
            return
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        df = pd.DataFrame(self.property_urls)
        df.to_csv(filepath, index=False)
        logger.info(f"💾 CSV saved with {len(df)} rows: {filepath}")
