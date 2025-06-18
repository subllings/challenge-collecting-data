import pandas as pd
import time
import random
import os
import logging
import json
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from seleniumwire import webdriver
from datetime import datetime


logger = logging.getLogger(__name__)

class ImmovlanUrlScraper:
    """
    ImmovlanScraper
    A class for scraping real estate property listing URLs from Immovlan for a given town, with support for pagination, session management, and output consolidation.
    
    Attributes:
        base_url (str): The base URL for the Immovlan search results.
        town (str): The name of the town to scrape listings for.
        max_pages (int): Maximum number of pages to scrape. If -1, scrape all available pages.
        delay_min (float): Minimum delay between requests (not actively used in this code).
        delay_max (float): Maximum delay between requests (not actively used in this code).
        run_id (str): Unique identifier for the scraping run. Defaults to current timestamp if not provided.
        output_dir (str): Directory where output files will be saved.
        driver (webdriver.Chrome): Selenium WebDriver instance for browser automation.
        property_urls (list): List of dictionaries containing scraped property URLs and metadata.
        data (list): Placeholder for additional data (not actively used in this code).

    Methods:
        _init_driver():
            Initializes and returns a configured Selenium Chrome WebDriver with request interception for blocking unwanted domains.
        restart_driver():
            Restarts the Selenium WebDriver, closing the current session and starting a new one.
        handle_cookie_banner():
            Attempts to dismiss the cookie consent banner if present on the page.
        scrape():
            Main entry point for scraping; initiates the process of collecting all listing URLs for the specified town.
        get_all_listing_urls(town_name: str):
            Iterates through paginated search results, collects property listing URLs, handles scrolling and session issues, and saves intermediate and final results to CSV and log files.
        close():
            Closes the Selenium WebDriver session safely.
        to_csv(filepath: str):
            Saves the collected property URLs to a CSV file at the specified path.
        consolidate_all_results(base_output_dir: str = "output", consolidated_dir_name: str = "consolidated_towns_urls"):
            Static method to combine all individual run CSVs into a single consolidated CSV, removing duplicates and saving summary statistics.
    
    Usage:
        scraper = ImmovlanScraper(base_url, town)
        scraper.scrape()
        scraper.close()
        ImmovlanScraper.consolidate_all_results()

    """


    def __init__(self, base_url: str, town: str, max_pages: int = -1, delay_min: float = 1.0, delay_max: float = 2.5, run_id: str = None, output_dir: str = "output", headless: bool = True):
        """
        Initializes the immovlan_scraper instance with the specified parameters.

        Args:
            base_url (str): The base URL of the website to scrape.
            town (str): The name of the town to filter property listings.
            max_pages (int, optional): The maximum number of pages to scrape. Defaults to -1 (no limit).
            delay_min (float, optional): The minimum delay (in seconds) between requests. Defaults to 1.0.
            delay_max (float, optional): The maximum delay (in seconds) between requests. Defaults to 2.5.
            run_id (str, optional): An identifier for the current run. If None, a timestamp is used. Defaults to None.
            output_dir (str, optional): Directory where output files will be saved. Defaults to "output".

        Attributes:
            base_url (str): The base URL for scraping.
            town (str): The town to search for properties.
            max_pages (int): The maximum number of pages to scrape.
            delay_min (float): Minimum delay between requests.
            delay_max (float): Maximum delay between requests.
            run_id (str): Identifier for the current run.
            output_dir (str): Directory for output files.
            driver: The Selenium WebDriver instance.
            property_urls (list): List to store property URLs.
            data (list): List to store scraped data.
            headless (bool): Flag to indicate if the browser should run in headless mode.
        """

        self.base_url = base_url
        """The base URL for scraping real estate listings."""
        
        self.town = town
        """The name of the town to scrape listings for."""
        
        self.max_pages = max_pages
        """Maximum number of pages to scrape. If -1, scrape all available pages."""
        
        self.delay_min = delay_min
        """Minimum delay between requests (in seconds)."""
        
        self.delay_max = delay_max
        """Maximum delay between requests (in seconds)."""
        
        self.run_id = run_id or datetime.now().strftime("%Y%m%d_%H%M")
        """Identifier for the current run."""
        
        self.output_dir = output_dir
        """List of dictionaries containing scraped property URLs and metadata."""
        
        self.headless = headless
        """Flag to indicate if the browser should run in headless mode."""  

        self.driver = self._init_driver()
        """List of dictionaries containing scraped property URLs and metadata."""
        
        self.property_urls = []
        """List of dictionaries containing scraped property URLs and metadata."""
        
        self.data = []
        """Placeholder for additional data (not actively used)."""
        


    def _init_driver(self):
        """
        Initializes and returns a Selenium Chrome WebDriver instance with custom options and a request interceptor.
        The driver is configured with:
            - A custom user-agent string.
            - Disabled extensions and GPU usage.
            - A fixed window size (1920x1080).
            - No sandbox and disabled shared memory usage for compatibility.
            - Selenium Wire options for in-memory request storage and disabled SSL verification.
        Additionally, a request interceptor is set up to block network requests to a predefined list of advertising, analytics, and tracking domains, as well as certain image and privacy-related domains.
        Returns:
            seleniumwire.webdriver.Chrome: Configured Chrome WebDriver instance with request interception.
        """
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

        if self.headless:
            options.add_argument("--headless=new")        

        # Initialize a Chrome WebDriver instance using Selenium Wire.
        # - `options`: defines Chrome launch settings (e.g., headless mode, user-agent, window size).
        # - `seleniumwire_options`: enables HTTP/HTTPS request capture and filtering via Selenium Wire.
        #   This allows the scraper to monitor, intercept, or block network traffic (e.g., ads, analytics).
        driver = webdriver.Chrome(options=options, seleniumwire_options=seleniumwire_options)

        # Define an interceptor to block unwanted third-party network requests.
        # This function is registered before any call to `.get()` to ensure all requests
        # can be filtered during page load.
        #
        # It blocks requests to known ad networks, analytics providers, and heavy external
        # resources (e.g., tracking scripts, image APIs), which improves scraping performance,
        # reduces page noise, and avoids unnecessary traffic.
        #
        # The list includes domains like:
        # - Advertising: doubleclick.net, pubmatic.com, googleads.g.doubleclick.net
        # - Analytics: google-analytics.com, optimizely.com, xiti.com
        # - Social/tracking: facebook.net, accounts.google.com
        # - Other: smartadserver.com, api-image.immovlan.be, etc.        
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
        """
        Restarts the Selenium WebDriver instance.

        Closes the current driver, if any, and initializes a new one.
        Logs a warning message indicating the driver is being restarted.
        """
        logger.warning("🔄 Restarting Selenium driver...")
        self.close()
        self.driver = self._init_driver()


    def handle_cookie_banner(self):
        """
        Attempts to dismiss the cookie banner on the current web page by clicking the accept button.

        Uses Selenium WebDriver to wait for a clickable element that likely represents a cookie consent button,
        identified by CSS selectors targeting buttons or elements with 'cookie' in their ID or class.
        Logs the outcome: whether the banner was dismissed, not found, or if an unexpected error occurred.

        Raises:
            Logs exceptions but does not propagate them.
        """
        try:
            accept_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button, [id*='cookie'], [class*='cookie']"))
            )
            accept_button.click()
            # Log a confirmation message once the cookie consent banner has been successfully dismissed 
            # (i.e., closed or rejected so it no longer blocks interaction with the page).            
            logger.info("✔️  Cookie banner dismissed (closed, no longer blocks interaction with the page)")
        except TimeoutException:
            logger.info("ℹ️ No cookie banner found.")
        except Exception as e:
            logger.warning("⚠️ Unexpected error while handling cookie banner: %s", e)

    def scrape(self):
        """
        Scrapes real estate listings for the specified town.

        Logs the start of the scraping process for the current town and retrieves all listing URLs associated with that town.

        Returns:
            None
        """
        logger.info("🔎 Scraping town: %s", self.town)
        self.get_all_listing_urls(town_name=self.town)

    def get_all_listing_urls(self, town_name: str):
        """
        Scrapes all property listing URLs for a given town from the target website, handling pagination, scrolling, 
        and session management. Saves found URLs and progress logs to disk, including partial CSVs per page and a 
        final CSV with all collected URLs.
        Args:
            town_name (str): The name of the town to search for property listings.
        Side Effects:
            - Creates a folder for the run, named with the town and run ID.
            - Writes progress and warnings to a log file.
            - Saves partial CSV files with URLs found on each page.
            - Saves a final CSV file with all unique property URLs found.
            - Writes a summary statistics file with run details.
        Behavior:
            - Iterates through paginated search results, visiting each page.
            - Handles session timeouts and restarts the driver if needed.
            - Scrolls to the bottom of each page to load all listings.
            - Extracts property URLs from both the DOM and XHR JSON responses.
            - Stops if too many consecutive empty or duplicate pages are encountered.
            - Logs and saves all relevant information for debugging and reproducibility.
        Raises:
            None directly, but logs and handles exceptions related to driver/session issues and page timeouts.
        """
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
                logger.info("👉📄 Visiting page %d: %s", page, full_url)
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
                            f"\n[{timestamp}] ⚫ Script stopped after {max_empty_pages} consecutive pages "
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
                            f"\n[{timestamp}] 🔵 Stopping: {max_same_pages} pages with identical links detected. Likely the end."
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
                            f"\n[{timestamp}] ⚫ Script stopped after {max_empty_pages} consecutive empty pages "
                            f"(last at page {page})."
                        )
                        logger.warning(stop_msg)
                        f.write(stop_msg + "\n")
                        break
                    continue
                else:
                    empty_pages_in_a_row = 0

                logger.info("[INFO] Found %d property links on page %d", len(page_links), page)
                f.write(f"[{timestamp}] [INFO] Found {len(page_links)} property links on page {page}\n")

                page_data = []
                for i, url in enumerate(page_links, 1):
                    #entry = {"page": page, "url": url}
                    entry = {"town": town_name, "page": page, "url": url}
                    if entry not in self.property_urls:
                        self.property_urls.append(entry)
                    page_data.append(entry)
                    logger.info("🟢 [%02d] URL found: %s", i, url)
                    f.write(f"[{timestamp}] 🟢 [{i:02d}] {url}\n")

                partial_csv_path = os.path.join(full_output_dir, f"partial_urls_page_{page}_{filename_base}.csv")
                
                pd.DataFrame(page_data, columns=["town", "page", "url"]).to_csv(partial_csv_path, index=False)
                logger.info("[INFO] ✅ Partial CSV saved: %s", partial_csv_path)
              
                page += 1

        final_csv = os.path.join(full_output_dir, f"urls_{filename_base}_records_{len(self.property_urls)}.csv")
        self.to_csv(filepath=final_csv)

        summary_path = os.path.join(full_output_dir, f"stats_{filename_base}.txt")
        with open(summary_path, "w", encoding="utf-8") as stats:
            stats.write(f"Run ID         : {self.run_id}\n")
            stats.write(f"Pages visited  : {page}\n")
            stats.write(f"Total listings : {len(self.property_urls)}\n")
            stats.write(f"Timestamp      : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        logger.info("📊 Stats saved to %s", summary_path)

    def close(self):
        """
        Closes the Selenium WebDriver instance.

        Attempts to gracefully quit the WebDriver. If an exception occurs during the process,
        a warning is logged with the error details.
        """
        try:
            self.driver.quit()
        except Exception as e:
            logger.warning("⚠️ Error while closing driver: %s", e)        

    def to_csv(self, filepath: str):
        """
        Saves the collected property URLs to a CSV file at the specified filepath.

        Parameters:
            filepath (str): The path where the CSV file will be saved.

        Behavior:
            - If there are no property URLs to save, logs a warning and returns.
            - Ensures the target directory exists.
            - Saves the property URLs as rows in a CSV file without the index.
            - Logs an info message with the number of rows saved and the file location.
        """
        if not self.property_urls:
            logger.warning("[WARNING] No URLs to save.")
            return
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        df = pd.DataFrame(self.property_urls)
        df.to_csv(filepath, index=False)
        logger.info("💾 CSV saved with %d rows: %s", len(df), filepath)


    @staticmethod
    def consolidate_all_results(base_output_dir: str = "output", consolidated_dir_name: str = "consolidated_towns_urls") -> None:
        """
        Consolidates all CSV files containing scraped URLs from a base output directory into a single CSV file.
        This function searches recursively within the specified `base_output_dir` for CSV files whose names start with "urls_" and end with ".csv". 
        It reads all found files, concatenates their contents into a single DataFrame, removes duplicate entries, and writes the consolidated data to a new timestamped CSV file in a newly created directory. 
        Additionally, it generates a statistics text file summarizing the consolidation process, including the number of files combined and the number of unique listings.
        Args:
            base_output_dir (str): The root directory to search for CSV files. Defaults to "output".
            consolidated_dir_name (str): The base name for the directory and consolidated CSV file. Defaults to "consolidated_towns_urls".
        Returns:
            None
        """
        logger.info("🧮 Consolidating all scraped results...")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        final_dir = os.path.join(base_output_dir, f"{consolidated_dir_name}_{timestamp}")
        os.makedirs(final_dir, exist_ok=True)

        all_data = []
        for root, dirs, files in os.walk(base_output_dir):
            for file in files:
                if file.startswith("urls_") and file.endswith(".csv"):
                    file_path = os.path.join(root, file)
                    logger.info("📥 Reading file: %s", file_path)
                    try:
                        df = pd.read_csv(file_path)
                        all_data.append(df)
                    except Exception as e:
                        logger.warning("⚠️ Could not read %s: %s", file_path, e)

        if not all_data:
            logger.warning("❌ No data files found to consolidate.")
            return

        combined_df = pd.concat(all_data, ignore_index=True)
        combined_df.drop_duplicates(inplace=True)

        consolidated_csv_name = f"{consolidated_dir_name}_{timestamp}.csv"
        consolidated_csv_path = os.path.join(final_dir, consolidated_csv_name)
        combined_df.to_csv(consolidated_csv_path, index=False)
        logger.info("✅ Consolidated CSV written: %s", consolidated_csv_path)

        stats_path = os.path.join(final_dir, f"stats_consolidation_{timestamp}.txt")
        with open(stats_path, "w", encoding="utf-8") as f:
            f.write(f"Files combined  : {len(all_data)}\n")
            f.write(f"Unique listings : {len(combined_df)}\n")
            f.write(f"Timestamp       : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        logger.info("📊 Consolidation stats written: %s", stats_path)
        logger.info("✅ All towns consolidated in one CSV.")



    


        