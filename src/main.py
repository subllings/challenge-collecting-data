import logging
import os
from pathlib import Path
import pandas as pd
from src.immovlan_url_scraper import ImmovlanUrlScraper 
from src.immovlan_details_scraper import ImmovlanDetailsScraper
import shutil

# Ensure folders exist
os.makedirs("output", exist_ok=True)
os.makedirs("data", exist_ok=True)

# Path to configuration file
TOWNS_CSV_PATH = Path("data/immovlan_towns_to_scrape.csv")

# Logger configuration
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(asctime)s — %(message)s",
    handlers=[
        logging.FileHandler("output/immovlan_scraper.log", mode="w", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Reduce seleniumwire verbosity
logging.getLogger('seleniumwire').setLevel(logging.WARNING)

def main():
    """
    Main entry point for the Immovlan scraper workflow.
    This function orchestrates the following steps based on configuration flags:
    1. Reads a list of towns from a CSV file and scrapes real estate URLs for each town.
    2. Consolidates all scraped results into a single CSV file.
    3. Extracts detailed real estate information from the consolidated URLs.
    Flags:
        - read_towns_url (bool): If True, reads towns from CSV and scrapes URLs for each town.
        - consolidate_all_tows_url (bool): If True, consolidates all town results into one CSV.
        - extract_details_from_consolidated (bool): If True, extracts detailed information from consolidated URLs.
    Logging is used to provide progress updates and error reporting.
    """
    read_towns_url = True
    consolidate_all_tows_url = True
    extract_details_from_consolidated = True

    logger.info("🚀 Starting Immovlan scraper")

    # ------------------------------------------------------------------------
    # Step 1: Load the list of towns to scrape from a CSV file.
    # The file should be located at: data/immovlan_towns_to_scrape.csv
    # Each town entry will be processed individually during the scraping loop
    # For each town, a subfolder named "<town_name>_<date_time>" will be created 
    # in the output directory.
    # ------------------------------------------------------------------------

    if read_towns_url:
      # Town url extration
      if not TOWNS_CSV_PATH.exists():
          logger.error("Configuration file not found: %s", TOWNS_CSV_PATH)
          return

      
      df = pd.read_csv(TOWNS_CSV_PATH)
      df["town"] = df["town"].astype(str).str.strip()  # Supprime les espaces début/fin
      df["town"] = df["town"].str.replace(" ", "", regex=False)  # Supprime les espaces au milieu 
      towns = df["town"].dropna().unique().tolist()
      logger.info("🌆 %d tow(s) to scrape: %s", len(towns), towns)

 
      for town in towns:
          url = (
              "https://immovlan.be/en/real-estate"
              "?transactiontypes=for-sale,in-public-sale"
              "&propertytypes=house,apartment"
              f"&municipals={town}&noindex=1"
          )
          logger.debug("🌐🌐🌐 URL used for %s: %s", town, url)

          logger.info("🔎 Scraping town: %s", town)
          scraper_urls = ImmovlanUrlScraper(base_url=url, town=town, headless=True, max_pages=-1)
          scraper_urls.scrape_and_save_urls()
          scraper_urls.close()

      logger.info("✅ All towns scraped successfully.")

    # ----------------------------------------------------------------
    # Step 2: Consolidate the full list of real estate listings from 
    # all towns in a csv file stored in a folder named 
    # "<_consolidated_towns_url>_<date_time>".
    # ----------------------------------------------------------------

    if consolidate_all_tows_url:
        ImmovlanUrlScraper.consolidate_all_results(base_output_dir="output", consolidated_dir_name="_consolidated_towns_urls")
        logger.info("✅ All towns consolidated in one CSV.")

    # ----------------------------------------------------------------
    # 3. For all url collected during step 2, extract details real estate 
    # and store them in a csv file in a folder named 
    # "_real_estate_details_<date_time>".
    # ----------------------------------------------------------------

    if extract_details_from_consolidated:
        scraper_details_properties = ImmovlanDetailsScraper(output_dir="output", headless=True, limit=10)
        scraper_details_properties.scrape_and_save_properties()
        scraper_details_properties.close()

        logger.info("👏 Real estate details extracted from consolidated URLs.")


if __name__ == "__main__":
    main()
