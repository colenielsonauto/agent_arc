"""
Pub/Sub background handler → AI pipeline.
Triggered by Pub/Sub topic: email-inbound
Cloud Functions gen‑1 style (entrypoint: pubsub_webhook)
"""
import base64
import json
import logging

from functions.ingest_email import ingest_email
from functions.analyze_email import analyze_email
from functions.forward_and_draft import forward_and_draft, get_gmail_service

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


def pubsub_webhook(event, context=None):
    """
    Background function triggered by Pub/Sub.
    `event` is the Pub/Sub message payload.
    """
    # Coerce any raw string payload into JSON FIRST
    if isinstance(event, str):
        event = json.loads(event)
    
    logger.info("Received Pub/Sub event: %s", event)


    # Normalize the base64 extraction to try both Gen-2 and Gen-1 envelopes
    raw_b64 = (
        event.get("message", {}).get("data")
        or event.get("data", {}).get("message", {}).get("data")
    )
    if not raw_b64:
        raise ValueError(f"Invalid Pub/Sub event: {event}")

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
