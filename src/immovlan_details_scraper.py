import os
import csv
import time
import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from src.utils.logger import logger


class ImmovlanDetailsScraper:
    def __init__(self, csv_file: str, output_dir: str = "output", limit: int = -1):
        self.csv_file = csv_file
        self.output_dir = output_dir
        self.limit = limit
        self.driver = self._init_driver()
        self.output_file = self._generate_output_file_path()

    def _init_driver(self):
        options = Options()
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        return webdriver.Chrome(options=options)

    def _generate_output_file_path(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        dir_path = os.path.join(self.output_dir, f"real_estate_details_{timestamp}")
        os.makedirs(dir_path, exist_ok=True)
        return os.path.join(dir_path, f"real_estate_details_{timestamp}.csv")

    def close(self):
        if hasattr(self, 'driver') and self.driver:
            self.driver.quit()


    def extract_all(self):
        logger.info(f"🔍 Reading from: {self.csv_file}")
        df = pd.read_csv(self.csv_file)
        if self.limit != -1:
            df = df.head(self.limit)

        fieldnames = [
            "town", "page", "url", "property_type", "price", "address", "postal_code", "city",
            "bedrooms", "bedroom1_surface", "bedroom2_surface", "bathrooms", "toilets",
            "surface_livable", "terrace", "terrace_surface", "terrace_orientation", "floor", "year_built",
            "condition", "kitchen_equipment", "cellar", "glazing_type", "elevator", "entry_phone",
            "epc_score", "epc_total", "epc_valid_until"
        ]

        with open(self.output_file, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for i, row in enumerate(df.itertuples(index=False), start=1):
                try:
                    self.driver.get(row.url)
                    time.sleep(2)
                    soup = BeautifulSoup(self.driver.page_source, "html.parser")

                    # Extract values from structured layout
                    def get_label_value(label):
                        element = soup.find("h4", string=label)
                        if element and element.find_next_sibling("p"):
                            return element.find_next_sibling("p").text.strip()
                        return None

                    details = {
                        "town": getattr(row, "town", ""),
                        "page": getattr(row, "page", ""),
                        "url": row.url,
                        "property_type": soup.select_one(".detail__header_title_main").text.strip().split()[0] if soup.select_one(".detail__header_title_main") else None,
                        "price": soup.select_one(".detail__header_price_data").text.strip() if soup.select_one(".detail__header_price_data") else None,
                        "address": soup.select_one(".detail__header_address").text.strip() if soup.select_one(".detail__header_address") else None,
                        "postal_code": None,
                        "city": None,
                        "bedrooms": get_label_value("Number of bedrooms"),
                        "bedroom1_surface": get_label_value("Surface bedroom 1"),
                        "bedroom2_surface": get_label_value("Surface bedroom 2"),
                        "bathrooms": get_label_value("Number of bathrooms"),
                        "toilets": get_label_value("Number of toilets"),
                        "surface_livable": get_label_value("Livable surface"),
                        "terrace": get_label_value("Terrace"),
                        "terrace_surface": get_label_value("Surface terrace"),
                        "terrace_orientation": get_label_value("Terrace orientation"),
                        "floor": get_label_value("Floor of appartment"),
                        "year_built": get_label_value("Build Year"),
                        "condition": get_label_value("State of the property"),
                        "kitchen_equipment": get_label_value("Kitchen equipment"),
                        "cellar": get_label_value("Cellar"),
                        "glazing_type": get_label_value("Type of glazing"),
                        "elevator": get_label_value("Elevator"),
                        "entry_phone": get_label_value("Entry phone"),
                        "epc_score": get_label_value("Specific primary energy consumption"),
                        "epc_total": get_label_value("Yearly total primary energy consumption"),
                        "epc_valid_until": get_label_value("Validity date EPC/PEB")
                    }

                    # Extract postal_code and city from address
                    address_parts = details["address"].split() if details["address"] else []
                    if len(address_parts) >= 2:
                        try:
                            details["postal_code"] = next(part for part in address_parts if part.isdigit())
                            details["city"] = address_parts[-1]
                        except StopIteration:
                            pass

                    writer.writerow(details)
                    logger.info(f"✅ [{i}/{len(df)}] Extracted: {row.url}")
                except Exception as e:
                    logger.warning(f"⚠️ Error extracting from {row.url}: {e}")

        logger.info(f"💾 Saved detailed data to: {self.output_file}")

