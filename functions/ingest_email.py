import base64, json
from flask import Request

def ingest_email(event, context=None):
    if 'data' in event:
        if event['data']:  # Check if data is not empty
            payload = base64.b64decode(event['data']).decode()
            msg = json.loads(payload)
        else:
            msg = {}  # Empty payload case
    elif hasattr(event, 'get_json'):
        # Flask Request object
        request: Request = event
        msg = request.get_json(force=True)
    else:
        # Direct dictionary input
        msg = event
    normalized = {
        "from": msg.get("from","unknown@domain.com"),
        "subject": msg.get("subject",""),
        "body": msg.get("body","")
    }
    print("Ingested:", normalized)
    return normalized 