import logging
import os
from pathlib import Path
import pandas as pd
from src.immovlan_scraper import ImmovlanScraper 
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
    read_towns_url = False
    consolidate_all_tows_url = False
    extract_details_from_consolidated = True


    logger.info("🚀 Starting Immovlan scraper")

    if read_towns_url:
      # Town url extration
      if not TOWNS_CSV_PATH.exists():
          logger.error(f"Configuration file not found: {TOWNS_CSV_PATH}")
          return

      
      df = pd.read_csv(TOWNS_CSV_PATH)
      df["town"] = df["town"].astype(str).str.strip()  # Supprime les espaces début/fin
      df["town"] = df["town"].str.replace(" ", "", regex=False)  # Supprime les espaces au milieu 
      towns = df["town"].dropna().unique().tolist()
      logger.info(f"🌆 {len(towns)} tows to scrape: {towns}")

      
      #towns = pd.read_csv(TOWNS_CSV_PATH)["immovlan_url_name"].dropna().str.strip().str.replace(" ", "", regex=False).unique().tolist()

      #logger.info(f"🌆 Total towns to scrape: {len(towns)}")

 
      for town in towns:
          url = (
              "https://immovlan.be/en/real-estate"
              "?transactiontypes=for-sale,in-public-sale"
              "&propertytypes=house,apartment"
              f"&municipals={town}&noindex=1"
          )
          logger.debug(f"🌐🌐🌐 URL used for {town}: {url}")

          logger.info(f"🔎 Scraping town: {town}")
          scraper = ImmovlanScraper(base_url=url, town=town, max_pages=-1)
          scraper.scrape()
          scraper.close()

      logger.info("✅ All towns scraped successfully.")

    # Consolidate all results for all towns
    if consolidate_all_tows_url:
        ImmovlanScraper.consolidate_all_results(base_output_dir="output", consolidated_dir_name="_consolidated_towns_urls")
        logger.info("✅ All towns consolidated in one csv.")

    # Extract details real estate from consolidated URLs
    if extract_details_from_consolidated:
        scraper_detail = ImmovlanDetailsScraper(output_dir="output", headless=True, limit=10)
        scraper_detail.extract_all()
        scraper_detail.close()

        logger.info("✅ Details extracted from consolidated URLs.")


if __name__ == "__main__":
    main()
