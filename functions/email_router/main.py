# Cloud Functions entry point for Email Router
import logging
import sys
import os
from typing import Any

# Add src directory to Python path for local imports
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, '..', '..', 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Setup centralized logging first
try:
    from email_router.config.logging_config import setup_logging
    logger = setup_logging()
    logger.info("Logging configured successfully")
except ImportError as e:
    # Fallback logging setup
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.warning(f"Could not import logging config: {e}")

try:
    from email_router.handlers.pubsub_handler import pubsub_webhook
    logger.info("Successfully imported pubsub_webhook")
except ImportError as e:
    logger.error(f"Failed to import pubsub_webhook: {e}")
    
    # Fallback implementation
    def pubsub_webhook(cloud_event: Any) -> str:
        logger.error("Using fallback pubsub_webhook due to import error")
        return "Error: Could not import email router"

# Export the function for Cloud Functions
__all__ = ['pubsub_webhook'] 