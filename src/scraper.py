# src/scraper.py
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict
from src.utils.config import HEADERS, BASE_URL


class ImmowebScraper:
    def __init__(self, property_type="HOUSE", pages=100, threads=10):
        self.property_type = property_type
        self.pages = pages
        self.threads = threads
        self.base_url = BASE_URL
        self.headers = HEADERS

    def fetch_page(self, page: int, city: str = "Brussels") -> List[Dict]:
        """
        Fetches data for a specific page and city from the API.

        Args:
            page (int): The page number to fetch.
            city (str): The city to filter results by (default is Brussels).

        Returns:
            List[Dict]: A list of property results,
            or an empty list if an error occurs.
        """
        params = {
            "countries": "BE",
            "propertyTypes": self.property_type,
            "offerTypes": "FOR_SALE",
            "page": page,
            "city": city  # Adding city parameter
        }
        try:
            # Sending the GET request
            response = requests.get(
                url=self.base_url,
                headers=self.headers,
                params=params,
                timeout=10
            )
            response.raise_for_status()  # Raise an HTTPError for bad responses
            data = response.json()

            # Extracting results
            results = data.get("results", {}).get(
                "propertySearch", {}
            ).get("result", [])
            print(
                f"[INFO] Successfully fetched page {page} for city {city} "
                f"with {len(results)} results."
            )
            return results

        except requests.exceptions.HTTPError as http_err:
            print(
                f"[ERROR] HTTP error occurred while fetching page {page}: "
                f"{http_err}"
            )
        except requests.exceptions.ConnectionError as conn_err:
            print(
                f"[ERROR] Connection error occurred while fetching "
                f"page {page}: {conn_err}"
            )
        except requests.exceptions.Timeout as timeout_err:
            print(
                f"[ERROR] Timeout occurred while fetching page {page}: "
                f"{timeout_err}"
            )
        except requests.exceptions.RequestException as req_err:
            print(
                f"[ERROR] General request error occurred while fetching "
                f"page {page}: {req_err}"
            )

        # Return an empty list in case of any error
        return []

    def run(self, city: str = "Brussels") -> List[Dict]:
        """
        Runs the scraper to fetch listings for the specified city.

        Args:
            city (str): The city to filter results by (default is Brussels).

        Returns:
            List[Dict]: A list of property listings.
        """
        listings = []
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            future_to_page = {
                executor.submit(self.fetch_page, page, city=city): page
                for page in range(1, self.pages + 1)
            }
            for future in as_completed(future_to_page):
                page = future_to_page[future]
                try:
                    results = future.result()
                    listings.extend(results)
                    print(
                        f"[✓] Page {page} scraped for city {city} "
                        f"({len(results)} results)"
                    )
                except Exception as e:
                    print(
                        f"[ERROR] Exception on page {page} for city {city}: "
                        f"{e}"
                    )
        return listings
