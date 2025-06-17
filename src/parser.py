# src/parser.py

from typing import Dict, Any

def parse_listing(listing: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parses a single Immoweb listing JSON into a clean dictionary with 20 standard fields.
    """
    try:
        result = {
            "Locality": listing.get("property", {}).get("location", {}).get("locality"),
            "Type of property": listing.get("property", {}).get("type"),
            "Subtype of property": listing.get("property", {}).get("subtype"),
            "Price": listing.get("price", {}).get("amount"),
            "Type of sale": listing.get("transaction", {}).get("sale", {}).get("type"),

            "Number of rooms": listing.get("property", {}).get("bedroomCount"),
            "Living Area": listing.get("property", {}).get("netHabitableSurface"),

            "Fully equipped kitchen": int(bool(listing.get("property", {}).get("kitchen", {}).get("type") == "INSTALLED")),
            "Furnished": int(bool(listing.get("transaction", {}).get("sale", {}).get("isFurnished"))),
            "Open fire": int(bool(listing.get("property", {}).get("fireplaceExists"))),

            "Terrace": int(bool(listing.get("property", {}).get("hasTerrace"))),
            "Terrace Area": listing.get("property", {}).get("terraceSurface"), 

            "Garden": int(bool(listing.get("property", {}).get("hasGarden"))),
            "Garden Area": listing.get("property", {}).get("gardenSurface"),

            "Surface of the land": listing.get("property", {}).get("landSurface"),
            "Surface area of the plot of land": listing.get("property", {}).get("plotSurface"),

            "Number of facades": listing.get("property", {}).get("facadeCount"),
            "Swimming pool": int(bool(listing.get("property", {}).get("hasSwimmingPool"))),
            "State of the building": listing.get("property", {}).get("building", {}).get("condition")
        }

        return {k: (v if v is not None else None) for k, v in result.items()}
    
    except Exception as e:
        print(f"[ERROR] Failed to parse listing: {e}")
        return {field: None for field in [
            "Locality", "Type of property", "Subtype of property", "Price", "Type of sale",
            "Number of rooms", "Living Area", "Fully equipped kitchen", "Furnished", "Open fire",
            "Terrace", "Terrace Area", "Garden", "Garden Area", "Surface of the land",
            "Surface area of the plot of land", "Number of facades", "Swimming pool", "State of the building"
        ]}
