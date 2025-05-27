# Cloud Functions entry wrapper
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from email_router.handlers.pubsub_handler import pubsub_webhook 