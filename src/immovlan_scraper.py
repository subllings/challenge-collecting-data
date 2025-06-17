from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from seleniumwire import webdriver
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin
import glob
import csv 

import pandas as pd
import time
import random
import os
import logging
import json

logger = logging.getLogger(__name__)

class ImmovlanScraper:
    def __init__(self, base_url: str, town: str, max_pages: int = -1, delay_min: float = 1.0, delay_max: float = 2.5, run_id: str = None, output_dir: str = "output"):
        self.base_url = base_url
        self.town = town
        self.max_pages = max_pages
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.run_id = run_id or datetime.now().strftime("%Y%m%d_%H%M")
        self.output_dir = output_dir
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

        driver = webdriver.Chrome(options=options, seleniumwire_options=seleniumwire_options)

        # Interceptor defined BEFORE any call to .get()
        def interceptor(request):
            blocked_domains = [
                'doubleclick.net',
                'googletagmanager.com',
                'google-analytics.com',
                'smartadserver.com',
                'optimizely.com',
                'facebook.net',
                'adsafeprotected.com',
                'pubmatic.com',
                'adservice.google.com',
                'adservice.google.be',
                'cm.g.doubleclick.net',
                'diff.smartadserver.com',
                'pagead2.googlesyndication.com',
                'securepubads.g.doubleclick.net',
                'api-image.immovlan.be',
                'xiti.com',
                'privacy-center.com',
                'accounts.google.com',
            ]
            if any(domain in request.url.lower() for domain in blocked_domains):
                request.abort()

        driver.request_interceptor = interceptor
        return driver

    def restart_driver(self):
        logger.warning("🔄 Restarting Selenium driver...")
        self.close()
        self.driver = self._init_driver()


    def handle_cookie_banner(self):
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

    def scrape(self):
        logger.info(f"🔎 Scraping town: {self.town}")
        self.get_all_listing_urls(town_name=self.town)

    def get_all_listing_urls(self, town_name: str):
        folder_name = f"{town_name}_{self.run_id}"

        full_output_dir = os.path.join(self.output_dir, folder_name)
        os.makedirs(full_output_dir, exist_ok=True)

        filename_base = f"{town_name}_{self.run_id}"
        output_log = os.path.join(full_output_dir, f"urls_by_page_{filename_base}.log")

        empty_pages_in_a_row = 0
        max_empty_pages = 3
        same_pages_in_a_row = 0
        max_same_pages = 10
        last_page_links = []

        with open(output_log, "w", encoding="utf-8") as f:
            page = 1
            while self.max_pages == -1 or page <= self.max_pages:
                full_url = f"{self.base_url}&page={page}"
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                logger.info(f"📄 Visiting page {page}: {full_url}")
                f.write(f"\n[{timestamp}] === Page {page} ===\n>>> Visiting: {full_url}\n")

                # Check that the session is active (prevents InvalidSessionIdException)
                try:
                    _ = self.driver.session_id
                except Exception:
                    logger.warning("⚠️ Driver session inactive — restarting.")
                    self.restart_driver()

                self.driver.get(full_url)

                self.driver.requests.clear()
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
                    page += 1
                    continue

                try:
                    last_height = self.driver.execute_script("return document.body.scrollHeight")
                except Exception:
                    logger.error("❌ Failed to get page height — session likely lost. Skipping page.")
                    break              
                
                while True:
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(random.uniform(1.5, 2.5))

                    try:
                        new_height = self.driver.execute_script("return document.body.scrollHeight")
                    except Exception:
                        logger.error("❌ Failed to scroll — session lost. Breaking scroll loop.")
                        break
                    
                    if new_height == last_height:
                        break
                    last_height = new_height

                links_dom = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/en/detail/')]")
                dom_links = {
                    elem.get_attribute("href").split("?")[0].strip()
                    for elem in links_dom
                    if elem.get_attribute("href") and "/en/detail/" in elem.get_attribute("href")
                }

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

                page_data = []
                for i, url in enumerate(page_links, 1):
                    #entry = {"page": page, "url": url}
                    entry = {"town": town_name, "page": page, "url": url}
                    if entry not in self.property_urls:
                        self.property_urls.append(entry)
                    page_data.append(entry)
                    logger.info(f"🟢 [{i:02d}] URL found: {url}")
                    f.write(f"[{timestamp}] 🟢 [{i:02d}] {url}\n")

                partial_csv_path = os.path.join(full_output_dir, f"partial_urls_page_{page}_{filename_base}.csv")
                #pd.DataFrame(page_data, columns=["page", "url"]).to_csv(partial_csv_path, index=False)
                pd.DataFrame(page_data, columns=["town", "page", "url"]).to_csv(partial_csv_path, index=False)
                logger.info(f"[INFO] ✅ Partial CSV saved: {partial_csv_path}")
              
                page += 1

        final_csv = os.path.join(full_output_dir, f"urls_{filename_base}_records_{len(self.property_urls)}.csv")
        self.to_csv(filepath=final_csv)

        summary_path = os.path.join(full_output_dir, f"stats_{filename_base}.txt")
        with open(summary_path, "w") as stats:
            stats.write(f"Run ID         : {self.run_id}\n")
            stats.write(f"Pages visited  : {page}\n")
            stats.write(f"Total listings : {len(self.property_urls)}\n")
            stats.write(f"Timestamp      : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        logger.info(f"📊 Stats saved to {summary_path}")

    def close(self):
        try:
            self.driver.quit()
        except Exception as e:
            logger.warning(f"⚠️ Error while closing driver: {e}")        

    def to_csv(self, filepath: str):
        if not self.property_urls:
            logger.warning("[WARNING] No URLs to save.")
            return
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        df = pd.DataFrame(self.property_urls)
        df.to_csv(filepath, index=False)
        logger.info(f"💾 CSV saved with {len(df)} rows: {filepath}")



    @staticmethod
    def consolidate_all_results(base_output_dir: str = "output", consolidated_dir_name: str = "consolidated_towns_urls") -> None:
        logger.info("🧮 Consolidating all scraped results...")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        final_dir = os.path.join(base_output_dir, f"{consolidated_dir_name}_{timestamp}")
        os.makedirs(final_dir, exist_ok=True)

        all_data = []
        for root, dirs, files in os.walk(base_output_dir):
            for file in files:
                if file.startswith("urls_") and file.endswith(".csv"):
                    file_path = os.path.join(root, file)
                    logger.info(f"📥 Reading file: {file_path}")
                    try:
                        df = pd.read_csv(file_path)
                        all_data.append(df)
                    except Exception as e:
                        logger.warning(f"⚠️ Could not read {file_path}: {e}")

        if not all_data:
            logger.warning("❌ No data files found to consolidate.")
            return

        combined_df = pd.concat(all_data, ignore_index=True)
        combined_df.drop_duplicates(inplace=True)

        consolidated_csv_name = f"{consolidated_dir_name}_{timestamp}.csv"
        consolidated_csv_path = os.path.join(final_dir, consolidated_csv_name)
        combined_df.to_csv(consolidated_csv_path, index=False)
        logger.info(f"✅ Consolidated CSV written: {consolidated_csv_path}")

        stats_path = os.path.join(final_dir, f"stats_consolidation_{timestamp}.txt")
        with open(stats_path, "w") as f:
            f.write(f"Files combined  : {len(all_data)}\n")
            f.write(f"Unique listings : {len(combined_df)}\n")
            f.write(f"Timestamp       : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        logger.info(f"📊 Consolidation stats written: {stats_path}")
        logger.info("✅ All towns consolidated in one CSV.")



    


        