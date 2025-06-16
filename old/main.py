import logging
from src.immoweb_scraper import ImmowebScraper
import os

# Créer dossier output si nécessaire
os.makedirs("output", exist_ok=True)
os.makedirs("data", exist_ok=True)

# Configuration du logger global
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(asctime)s — %(message)s",
    handlers=[
        logging.FileHandler("output/immoweb_scraper.log", mode='w', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    logger.info("▶️ Starting Immoweb scraper (Playwright version)")

    base_url = "https://www.immoweb.be/en/search/house/for-sale/brussels/province"
    scraper = ImmowebScraper(base_url=base_url, max_pages=2)

 

    logger.info("Starting to fetch property links with Playwright...")
    scraper.fetch_property_links_playwright()
    logger.info(f"Total links found: {len(scraper.property_urls)}")

    logger.info("Starting to fetch property details with Playwright...")
    scraper.fetch_property_details_playwright()

    logger.info("Saving data to CSV...")
    scraper.to_csv("data/output.csv")

    logger.info("Scraping finished successfully.")

if __name__ == "__main__":
    main()
