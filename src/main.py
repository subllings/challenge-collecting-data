import logging
import os
from pathlib import Path
import pandas as pd
from src.immovlan_scraper import ImmovlanScraper  

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
    logger.info("🚀 Starting Immovlan scraper")

    if not TOWNS_CSV_PATH.exists():
        logger.error(f"Configuration file not found: {TOWNS_CSV_PATH}")
        return

    towns = pd.read_csv(TOWNS_CSV_PATH)["immovlan_url_name"].dropna().unique().tolist()
    logger.info(f"📍 Total towns to scrape: {len(towns)}")

    for town in towns:
        url = (
            "https://immovlan.be/en/real-estate"
            "?transactiontypes=for-sale,in-public-sale"
            "&propertytypes=house,apartment"
            f"&municipals={town}&noindex=1"
        )
        logger.info(f"🔎 Scraping town: {town}")
        scraper = ImmovlanScraper(base_url=url, town=town, max_pages=1)
        scraper.scrape()
        scraper.close()

    logger.info("✅ All towns scraped successfully.")

if __name__ == "__main__":
    main()
