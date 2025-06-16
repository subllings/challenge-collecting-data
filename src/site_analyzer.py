import os
import logging
from urllib.parse import urljoin
from src.scraper import Scraper
from src.parser import parse_html

# Ensure the output directory exists
os.makedirs("output", exist_ok=True)

# Configure the logger to write to a file
logging.basicConfig(
    filename="output/site_analyzer.log",
    filemode="w",  # Overwrite each time
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def analyze_site_structure(base_url: str):
    """
    Analyze a website's structure for key SEO-related elements.
    Logs title, H1, robots meta tag, robots.txt content, and internal links.
    """
    scraper = Scraper(base_url)
    html = scraper.fetch_html()
    if not html:
        logger.error("❌ Unable to retrieve HTML content from base URL.")
        return

    soup = parse_html(html)

    # Extract <title> and first <h1>
    title = soup.find("title")
    h1 = soup.find("h1")
    logger.info("🔎 Title: %s", title.text.strip() if title else "Not found")
    logger.info("🔎 H1: %s", h1.text.strip() if h1 else "Not found")

    # Check for <meta name="robots">
    meta = soup.find("meta", {"name": "robots"})
    logger.info("🔎 Meta robots: %s", meta.get("content") if meta else "Not found")

    # Fetch and log robots.txt content
    robots_url = urljoin(base_url, "/robots.txt")
    robots_content = scraper.fetch_html(robots_url)
    if robots_content:
        logger.info("📄 robots.txt found:\n%s", robots_content.strip())
    else:
        logger.warning("❌ No robots.txt file found.")

    # Extract internal links
    links = [a["href"] for a in soup.find_all("a", href=True)]
    logger.info("🔗 %d internal links found.", len(links))
