import logging
from datetime import datetime
from src.immovlan_scraper import ImmovlanScraper  # Adjust the path if needed

# Generate a timestamp ID for this run
log_id = datetime.now().strftime("%Y%m%d_%H%M")

# Configure logging: one file per run, with timestamp in the filename
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(f"output/immovlan_run_{log_id}.log", mode="a", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

# Define postal codes and towns
postal_towns = {
    "1070": "anderlecht", "1082": "berchem-sainte-agathe", "1040": "etterbeek", "1140": "evere",
    "1083": "ganshoren", "1050": "elsene", "1081": "koekelberg", "1080": "sint-jans-molenbeek",
    "1060": "sint-gillis", "1210": "sint-joost-ten-node", "1180": "ukkel", "1170": "watermaal-bosvoorde",
    "1200": "woluwe-saint-lambert", "1150": "sint-pieters-woluwe", "1410": "waterloo", "1310": "la-hulpe",
    "1950": "kraainem", "1970": "wezembeek-oppem", "3090": "overijse", "2950": "kapellen",
    "3600": "genk", "2300": "turnhout"
}

municipals = (
    "brussels,braine-l-alleud,nivelles,wavre,ottignies-louvain-la-neuve,"
    "rixensart,lasne,chaumont-gistoux,zaventem,vilvoorde,tervuren,dilbeek,grimbergen,"
    "halle,sint-pieters-leeuw,villers-la-ville,genappe,zemst,kortenberg,rotselaar,nijlen,"
    "leuven,liege,namur,charleroi,la-louviere,mons,tournai,hasselt,mechelen,sint-niklaas,"
    "kortrijk,roeselare,aalst,dendermonde,marche-en-famenne,arlon"
)


# Suppress verbose Selenium-Wire logs
logging.getLogger("seleniumwire").setLevel(logging.WARNING)

def run_scraper():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logging.info(f"🚀 Starting Immovlan scraper at {timestamp}")

    for postal_code, town_name in postal_towns.items():
        # Build dynamic base URL per commune
        base_url = (
            "https://immovlan.be/en/real-estate"
            "?transactiontypes=for-sale,in-public-sale"
            "&propertytypes=apartment,house"
            "&propertysubtypes=apartment,studio,penthouse,ground-floor,duplex,loft,triplex,"
            "residence,villa,mixed-building,master-house,bungalow,cottage,mansion,chalet"
            f"&towns={postal_code}-{town_name.replace(' ', '-')}"
            f"&municipals={municipals}"
            "&noindex=1"
        )

        logging.info(f"🌍 Scraping {postal_code} - {town_name}...")
        scraper = ImmovlanScraper(base_url=base_url, max_pages=10000, run_id=log_id)
        scraper.get_all_listing_urls(postal_code=postal_code, town_name=town_name)
        scraper.close()

        total = len(scraper.property_urls)
        logging.info(f"✅ Completed {postal_code} - {town_name}: {total} URLs")

if __name__ == "__main__":
    run_scraper()
