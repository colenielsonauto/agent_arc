import base64, json
from flask import Request

def ingest_email(event, context=None):
    """
    Stub out Pub/Sub / Gmail watch logic with test data
    for local validation of end-to-end flow
    """
    # Return test data to validate the flow
    normalized = {
        "from": "test@domain.com",
        "subject": "Test",
        "body": "Hello world"
    }
    print("Ingested:", normalized)
    return normalized 