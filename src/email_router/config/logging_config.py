"""
Centralized logging configuration for Email Router.
"""

import logging
import sys


def setup_logging(level=logging.INFO):
    """
    Setup centralized logging configuration.
    Only call this once at application startup.
    """
    # Only configure if not already configured
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(
            level=level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler(sys.stdout)],
        )

    # Set specific loggers
    logger = logging.getLogger("email_router")
    logger.setLevel(level)

    # Reduce noise from external libraries
    logging.getLogger("google").setLevel(logging.WARNING)
    logging.getLogger("googleapiclient").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    return logger


def get_logger(name):
    """Get a logger instance for a specific module."""
    return logging.getLogger(f"email_router.{name}")
