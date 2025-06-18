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
    """
    
    def __init__(self, base_url: str, town: str, max_pages: int = -1, delay_min: float = 1.0, delay_max: float = 2.5, run_id: str = None, output_dir: str = "output", headless: bool = True):
        """
        Initializes the immovlan_scraper instance with the specified parameters.
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
            # Wait up to 5 seconds for a clickable element related to cookie consent to appear.
            # The selector targets any <button> or elements with IDs or classes containing "cookie".
            accept_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button, [id*='cookie'], [class*='cookie']"))
            )

             # If found and clickable, click the button to dismiss the banner.
            accept_button.click()

            # Log a confirmation message once the cookie consent banner has been successfully dismissed 
            # (i.e., closed or rejected so it no longer blocks interaction with the page).            
            logger.info("✔️  Cookie banner dismissed (closed, no longer blocks interaction with the page)")

        except TimeoutException:
            # If no cookie banner appears within 5 seconds, log that none was found.
            logger.info("ℹ️ No cookie banner found.")
        
        except Exception as e:
            # Catch and log any unexpected error that occurred during this process.
            logger.warning("⚠️ Unexpected error while handling cookie banner: %s", e)

    def scrape_and_save_urls(self):
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

                # Check that the current Selenium driver session is still active.
                # This is crucial to prevent errors such as InvalidSessionIdException
                # that occur if the browser has crashed or the session was lost unexpectedly.                
                try:
                    _ = self.driver.session_id # Accessing the session_id will raise if the session is invalid
                except Exception:
                    # Log a warning and restart the driver if the session is no longer valid.
                    # This allows the scraper to recover without crashing.
                    logger.warning("⚠️ Driver session inactive — restarting.")
                    self.restart_driver()

                # Navigate the Selenium driver to the full URL of the real estate listing
                self.driver.get(full_url)

                # Clear all previously stored requests captured by Selenium Wire
                # This ensures that only the network traffic for the current page is recorded
                self.driver.requests.clear()

                # Handle the cookie consent banner if it appears
                # This step ensures that the banner does not block further interaction with the page                
                self.handle_cookie_banner()

                try:
                    # Wait up to 10 seconds for at least one real estate listing link to be present on the page.
                    # The selector targets any anchor tag with '/en/detail/' in the href, which identifies valid listings.
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/en/detail/']"))
                    )
                except TimeoutException:
                    # If no valid listing links are found within 10 seconds, log a warning and mark the page as empty
                    msg = f"[WARNING] Timeout on page {page}. Page structure not recognized. Skipping."
                    logger.warning(msg)
                    f.write(f"[{timestamp}] {msg}\n")

                    # Increment the counter for consecutive empty pages
                    empty_pages_in_a_row += 1

                    # If too many consecutive empty pages are encountered, stop the scraping process
                    if empty_pages_in_a_row >= max_empty_pages:
                        stop_msg = (
                            f"\n[{timestamp}] ⚫ Script stopped after {max_empty_pages} consecutive pages "
                            f"with no valid listings (last at page {page})."
                        )
                        logger.warning(stop_msg)
                        f.write(stop_msg + "\n")
                        break # Exit the pagination loop
                    page += 1
                    continue # Skip to the next page

                try:
                    # Attempt to retrieve the total scroll height of the current web page using JavaScript.
                    # This is often used to determine if dynamic content (e.g., lazy-loaded listings) needs to be scrolled into view.
                    last_height = self.driver.execute_script("return document.body.scrollHeight")
                except Exception:
                    # If the call fails (e.g., due to session loss or browser crash), log the error and skip this page.
                    logger.error("❌ Failed to get page height — session likely lost. Skipping page.")
                    break # Exit the loop and move on to the next town or operation             
                
                # Continuously scroll down the page to load additional dynamic content (e.g., lazy-loaded listings)
                while True:
                    # Scroll to the bottom of the current page
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

                     # Wait for a random interval to mimic human behavior and allow content to load
                    time.sleep(random.uniform(1.5, 2.5))

                    try:
                        # Get the new scroll height after the scroll action
                        new_height = self.driver.execute_script("return document.body.scrollHeight")
                    except Exception:
                        # If unable to retrieve scroll height (e.g., session expired), log the issue and exit the loop
                        logger.error("❌ Failed to scroll — session lost. Breaking scroll loop.")
                        break
                    
                    # If scroll height did not change, no new content was loaded. Exit scrolling loop
                    if new_height == last_height:
                        break
                    
                    # Update the last known height to compare in the next iteration
                    last_height = new_height

                # Locate all anchor elements (<a>) on the page whose href attribute contains "/en/detail/"
                # These typically correspond to links to individual real estate property listings
                links_dom = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/en/detail/')]")
                
                # Build a set of cleaned and deduplicated listing URLs:
                # - Extract the href attribute from each element
                # - Remove any query parameters (e.g., ?ref=tracking_id) by splitting on "?"
                # - Strip leading/trailing whitespace
                # - Ensure the href is valid and contains the expected substrin                
                dom_links = {
                    elem.get_attribute("href").split("?")[0].strip()
                    for elem in links_dom
                    if elem.get_attribute("href") and "/en/detail/" in elem.get_attribute("href")
                }

                # Sort the list of links extracted from the current page's DOM to ensure consistent comparison
                page_links = sorted(dom_links)

                # Check whether the current page's links are exactly the same as the previous page's
                if page_links == last_page_links:
                    
                    # If so, increment the counter that tracks how many consecutive pages have the same links
                    same_pages_in_a_row += 1

                    # Prepare a warning message indicating duplicate pages have been detected
                    msg = f"[WARNING] Same links as previous page at page {page} ({same_pages_in_a_row} in a row)."
                    
                    # Log the warning message for debugging and analysis
                    logger.warning(msg)

                    # Write the warning message to a log file with a timestamp
                    f.write(f"[{timestamp}] {msg}\n")

                    # If too many pages in a row are duplicates, assume scraping has reached the end
                    if same_pages_in_a_row >= max_same_pages:
                        # Prepare a stop message to explain why the scraping is being stopped
                        stop_msg = (
                            f"\n[{timestamp}] 🔵 Stopping: {max_same_pages} pages with identical links detected. Likely the end."
                        )
                        logger.warning(stop_msg)
                        f.write(stop_msg + "\n")
                        break
                else:
                    # If the current page's links differ from the previous page, reset the duplicate counter
                    same_pages_in_a_row = 0
                
                # Save the current page's links as the "last seen" for comparison on the next iteration
                last_page_links = page_links

                # Check if the current page contains no property links at all
                # (page number is not relevant, bigger than the maximum pages available on the website)
                if not page_links:

                    # Prepare a warning message indicating that no links were found on this page
                    msg = f"[WARNING] No property links found on page {page}."

                     # Log the warning for debugging or monitoring purposes
                    logger.warning(msg)

                     # Write the warning message to the log file with a timestamp
                    f.write(f"[{timestamp}] {msg}\n")

                    # Increment the counter tracking how many empty pages have been seen in a row
                    empty_pages_in_a_row += 1
                    if empty_pages_in_a_row >= max_empty_pages:
                        
                        # Prepare a stop message explaining why the scraper is being stopped
                        stop_msg = (
                            f"\n[{timestamp}] ⚫ Script stopped after {max_empty_pages} consecutive empty pages "
                            f"(last at page {page})."
                        )
                         # Log the stopping reason
                        logger.warning(stop_msg)

                        # Also write this reason to the output log file
                        f.write(stop_msg + "\n")

                        # Exit the scraping loop
                        break

                    # Skip the rest of the loop and move to the next page
                    continue
                else:
                    # If the page had property links, reset the empty page counter
                    empty_pages_in_a_row = 0

                # Log an info message showing how many property links were found on the current page
                logger.info("[INFO] Found %d property links on page %d", len(page_links), page)

                # Write the same information to the log file with a timestamp
                f.write(f"[{timestamp}] [INFO] Found {len(page_links)} property links on page {page}\n")

                # Initialize a list to hold the URLs collected from the current page
                page_data = []

                # Iterate through all links found on the page, with enumeration starting at 1 for display purposes
                for i, url in enumerate(page_links, 1):

                    # Create a dictionary entry containing the town name, page number, and property URL
                    entry = {"town": town_name, "page": page, "url": url}

                    # Add the entry to the main list of all discovered property URLs, avoiding duplicates
                    if entry not in self.property_urls:
                        self.property_urls.append(entry)
                    
                    # Add the entry to the current page's data list
                    page_data.append(entry)

                    # Log each individual URL found, with an index (e.g., [01], [02], etc.)
                    logger.info("🟢 [%02d] URL found: %s", i, url)

                    # Write the URL to the log file as well, with the timestamp and index
                    f.write(f"[{timestamp}] 🟢 [{i:02d}] {url}\n")

                # Construct the output path for the partial CSV containing links from the current page
                partial_csv_path = os.path.join(full_output_dir, f"partial_urls_page_{page}_{filename_base}.csv")
                
                # Save the collected links for the current page into a CSV file (columns: town, page, url)
                pd.DataFrame(page_data, columns=["town", "page", "url"]).to_csv(partial_csv_path, index=False)

                # Log that the partial CSV was successfully saved
                logger.info("[INFO] ✅ Partial CSV saved: %s", partial_csv_path)
              
                page += 1

        # Define the path for the final CSV file containing all collected property URLs
        # The filename includes the base name and total number of records for traceability
        final_csv = os.path.join(full_output_dir, f"urls_{filename_base}_records_{len(self.property_urls)}.csv")
        
        # Export all collected property URLs to the final CSV file
        self.to_csv(filepath=final_csv)

        # Define the path for the summary statistics file
        # This will log high-level information about the scraping sessio
        summary_path = os.path.join(full_output_dir, f"stats_{filename_base}.txt")
        
        # Open the summary file in write mode with UTF-8 encoding
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



    


        