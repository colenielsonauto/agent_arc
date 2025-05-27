"""
Pub/Sub background handler → AI pipeline.
Triggered by Pub/Sub topic: email-inbound
Cloud Functions gen‑2 style (entrypoint: pubsub_webhook)
"""
import base64
import json
import logging
from cloudevents.http import CloudEvent
import functions_framework

from ..core.ingest_email import ingest_email
from ..core.analyze_email import analyze_email
from ..core.forward_and_draft import forward_and_draft, get_gmail_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fetch_and_ingest_emails(gmail_event):
    logger.info(f"Gmail event received: {gmail_event}")
    history_id = gmail_event.get("historyId")
    if not history_id:
        logger.error("No historyId in Gmail event")
        raise ValueError("Missing historyId in Gmail push notification")

    try:
        service = get_gmail_service()
        if not service:
            logger.warning("Gmail service unavailable — falling back to ingest_email")
            return ingest_email(gmail_event)

        resp = (
            service.users()
            .history()
            .list(userId="me", startHistoryId=history_id, labelId="INBOX")
            .execute()
        )
        records = resp.get("history", [])
        logger.info(f"Found {len(records)} history records since {history_id}")

        for rec in records:
            for added in rec.get("messagesAdded", []):
                msg = added.get("message", {})
                msg_id = msg.get("id")
                if msg_id:
                    logger.info(f"Fetching full message {msg_id}")
                    full_msg = (
                        service.users()
                        .messages()
                        .get(userId="me", id=msg_id, format="full")
                        .execute()
                    )
                    return ingest_email(full_msg, context="gmail_api")

        logger.info("No new messages found in history")
        return None

    except Exception as e:
        logger.error(f"Error fetching Gmail messages: {e}")
        logger.info("Falling back to ingest_email with raw event")
        return ingest_email(gmail_event)


@functions_framework.cloud_event
def pubsub_webhook(cloud_event: CloudEvent):
    """
    Background function triggered by Pub/Sub CloudEvent.
    `cloud_event` is the CloudEvent containing the Pub/Sub message.
    """
    logger.info("Received CloudEvent: %s", cloud_event)
    
    # Extract the Pub/Sub message from the CloudEvent
    try:
        # CloudEvent.data contains the Pub/Sub message
        pubsub_message = cloud_event.data
        
        # Handle both string and dict formats
        if isinstance(pubsub_message, str):
            pubsub_message = json.loads(pubsub_message)
            
        logger.info("Extracted Pub/Sub message: %s", pubsub_message)
        
        # Extract the base64-encoded Gmail notification
        # For CloudEvents, the structure is: cloud_event.data['message']['data']
        raw_b64 = pubsub_message.get("message", {}).get("data")
        
        if not raw_b64:
            raise ValueError(f"Invalid Pub/Sub message structure: {pubsub_message}")
            
    except Exception as e:
        logger.error("Error extracting Pub/Sub message from CloudEvent: %s", e)
        raise ValueError(f"Invalid CloudEvent format: {e}")

    try:
        raw = base64.b64decode(raw_b64)
        gmail_event = json.loads(raw)
        logger.info("Parsed Gmail event: %s", gmail_event)
    except Exception as e:
        logger.error("Decode/parse error: %s", e)
        raise ValueError(f"Invalid message.data: {e}")

    try:
        logger.info("Starting email processing pipeline")

        email_dict = fetch_and_ingest_emails(gmail_event)
        if not email_dict:
            logger.info("No new emails to process; exiting")
            return

        logger.info("Ingested email: %s", email_dict.get("subject", "(no subject)"))

        analysis = analyze_email(email_dict)
        logger.info("Classified as: %s", analysis["classification"])

        result = forward_and_draft(analysis)
        logger.info("Forwarded to: %s", result["forwarded_to"])

        logger.info("Pipeline completed successfully")

    except Exception as e:
        logger.error("Pipeline error: %s", e)
        # Re‑raise to trigger Pub/Sub retry
        raise
