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


