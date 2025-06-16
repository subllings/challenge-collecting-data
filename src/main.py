from immovlan_scraper import ImmovlanScraper
import logging
import os
from datetime import datetime

# Create logs & output directory if not exists
os.makedirs("output", exist_ok=True)
os.makedirs("logs", exist_ok=True)

# Log file with timestamp
log_filename = datetime.now().strftime("immovlan_%Y-%m-%d_%H-%M.log")
log_path = os.path.join("output", log_filename)

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(asctime)s — %(message)s',
    handlers=[
        logging.FileHandler(log_path, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    base_url = "https://immovlan.be/en/real-estate?transactiontypes=for-sale,in-public-sale&propertytypes=house,apartment&municipals=brussels&noindex=1"
    scraper = ImmovlanScraper(base_url=base_url, max_pages=2)

    try:
        urls = scraper.get_all_listing_urls()
        scraper.to_csv("output/immovlan_urls.csv")
    finally:
        scraper.close()