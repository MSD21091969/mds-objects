import logging
import sys
import os
from google.cloud import logging as cloud_logging

def setup_logging():
    # Define handlers for both stream and a fresh file on each run
    # The 'w' mode ensures the log file is truncated (cleared) on each start
    handlers = [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("server.log", mode='w') 
    ]

    # Basic configuration for local terminal logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers
    )

    # Attach Google Cloud Logging handler
    # Attach Google Cloud Logging handler
    # try:
    #     client = cloud_logging.Client()
    #     handler = client.get_default_handler()
    #     root_logger = logging.getLogger()
    #     root_logger.addHandler(handler)
    #     logging.info("Google Cloud Logging handler attached.")
    # except Exception as e:
    #     logging.warning(f"Could not attach Google Cloud Logging handler: {e}")
    # Conditionally attach Google Cloud Logging handler
    if os.getenv("ENABLE_CLOUD_LOGGING", "false").lower() == "true":
        try:
            client = cloud_logging.Client()
            handler = client.get_default_handler()
            root_logger = logging.getLogger()
            root_logger.addHandler(handler)
            logging.info("Google Cloud Logging handler attached.")
        except Exception as e:
            logging.warning(f"Could not attach Google Cloud Logging handler: {e}")

    # Set higher logging level for some noisy libraries if needed
    logging.getLogger("google.cloud.firestore").setLevel(logging.WARNING)
    logging.getLogger("google.api_core.bidi").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.info("Basic application logging configured.")
