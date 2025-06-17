import logging
import os

# Remove all handlers inherited from the root logger
logging.getLogger().handlers.clear()

# Create output directory if it doesn't exist
os.makedirs("output", exist_ok=True)

# Create logger
logger = logging.getLogger("site_logger")
logger.setLevel(logging.INFO)
logger.propagate = False  # Disable propagation to the root logger

# Only add handlers if none are present
if not logger.hasHandlers():
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # File handler
    file_handler = logging.FileHandler("output/site_analyzer.log", mode='w', encoding="utf-8")
    file_handler.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # Add both handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
