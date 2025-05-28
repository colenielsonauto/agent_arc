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

# Use existing logger without reconfiguring
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

        logger.info(
            f"Successfully authenticated with Gmail API, "
            f"fetching history since {history_id}"
        )

        # Try to fetch history - this is where many failures occur
        try:
            resp = (
                service.users()
                .history()
                .list(userId="me", startHistoryId=history_id, labelId="INBOX")
                .execute()
            )
        except Exception as history_error:
            logger.error(f"Gmail History API error: {history_error}")
            logger.info(
                "History API failed, attempting to fetch recent messages directly"
            )

            # Fallback: get recent messages directly
            try:
                recent_resp = (
                    service.users()
                    .messages()
                    .list(userId="me", labelIds=["INBOX"], maxResults=5)
                    .execute()
                )
                messages = recent_resp.get("messages", [])
                if messages:
                    # Get the most recent message
                    latest_msg_id = messages[0]["id"]
                    logger.info(f"Fetching latest message {latest_msg_id} as fallback")
                    full_msg = (
                        service.users()
                        .messages()
                        .get(userId="me", id=latest_msg_id, format="full")
                        .execute()
                    )
                    return ingest_email(full_msg, context="gmail_api")
            except Exception as fallback_error:
                logger.error(f"Fallback message fetch also failed: {fallback_error}")

            # Final fallback to test data processing
            logger.warning(
                "All Gmail API methods failed, falling back to ingest_email with event"
            )
            return ingest_email(gmail_event)

        records = resp.get("history", [])
        logger.info(f"Found {len(records)} history records since {history_id}")

        # Process history records
        processed_any = False
        for rec in records:
            for added in rec.get("messagesAdded", []):
                msg = added.get("message", {})
                msg_id = msg.get("id")
                if msg_id:
                    logger.info(f"Fetching full message {msg_id}")
                    try:
                        full_msg = (
                            service.users()
                            .messages()
                            .get(userId="me", id=msg_id, format="full")
                            .execute()
                        )
                        logger.info(
                            f"Successfully fetched message {msg_id} from Gmail API"
                        )
                        processed_any = True
                        return ingest_email(full_msg, context="gmail_api")
                    except Exception as msg_error:
                        logger.error(f"Failed to fetch message {msg_id}: {msg_error}")
                        continue

        if not processed_any:
            logger.info(
                "No new messages found in history or failed to process any messages"
            )
            # Check if this might be a test scenario
            if gmail_event.get("emailAddress") == "testingemailrouter@gmail.com":
                logger.info(
                    "This appears to be a test email notification, "
                    "processing as test data"
                )
                return ingest_email(gmail_event)

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
    logger.info("CloudEvent type: %s", getattr(cloud_event, "type", "unknown"))
    logger.info("CloudEvent source: %s", getattr(cloud_event, "source", "unknown"))
    logger.info("CloudEvent subject: %s", getattr(cloud_event, "subject", "unknown"))

    # Extract the Pub/Sub message from the CloudEvent
    try:
        # CloudEvent.data contains the Pub/Sub message
        pubsub_message = cloud_event.data
        logger.info("CloudEvent data type: %s", type(pubsub_message))
        logger.info("CloudEvent data: %s", pubsub_message)

        # Also log all CloudEvent attributes for debugging
        logger.info(
            "CloudEvent attributes: %s",
            {
                attr: getattr(cloud_event, attr, None)
                for attr in dir(cloud_event)
                if not attr.startswith("_")
            },
        )

        # Handle both string and dict formats
        if isinstance(pubsub_message, str):
            pubsub_message = json.loads(pubsub_message)

        logger.info("Extracted Pub/Sub message: %s", pubsub_message)

        # Extract the base64-encoded Gmail notification
        # Try different possible structures for CloudEvents
        raw_b64 = None

        # Structure 1: cloud_event.data['message']['data'] (standard Pub/Sub CloudEvent)
        if isinstance(pubsub_message, dict) and "message" in pubsub_message:
            message_data = pubsub_message.get("message", {})
            raw_b64 = message_data.get("data")
            logger.info(
                "Found data in message.data structure: %s",
                raw_b64[:50] if raw_b64 else "None",
            )
            logger.info("Full message structure: %s", message_data)
        # Structure 2: cloud_event.data['data'] (direct data)
        elif isinstance(pubsub_message, dict) and "data" in pubsub_message:
            raw_b64 = pubsub_message.get("data")
            logger.info(
                "Found data in direct data structure: %s",
                raw_b64[:50] if raw_b64 else "None",
            )
        # Structure 3: cloud_event.data is the base64 data directly
        elif isinstance(pubsub_message, str):
            raw_b64 = pubsub_message
            logger.info(
                "Using data as direct base64 string: %s",
                raw_b64[:50] if raw_b64 else "None",
            )
        # Structure 4: For gen2 functions, the data might be directly in
        # cloud_event.data
        else:
            logger.info("Trying to extract data directly from CloudEvent")
            # Check if cloud_event has data attribute directly
            if hasattr(cloud_event, "data") and cloud_event.data:
                cloud_data = cloud_event.data
                if isinstance(cloud_data, dict) and "data" in cloud_data:
                    raw_b64 = cloud_data["data"]
                    logger.info(
                        "Found data in cloud_event.data['data']: %s",
                        raw_b64[:50] if raw_b64 else "None",
                    )
                elif isinstance(cloud_data, str):
                    raw_b64 = cloud_data
                    logger.info(
                        "Found data as string in cloud_event.data: %s",
                        raw_b64[:50] if raw_b64 else "None",
                    )

        if not raw_b64:
            logger.error("Could not find base64 data in CloudEvent structure")
            logger.error("CloudEvent type: %s", type(cloud_event))
            logger.error(
                "CloudEvent data type: %s", type(getattr(cloud_event, "data", None))
            )
            logger.error("CloudEvent data: %s", getattr(cloud_event, "data", None))
            logger.error("Pubsub message: %s", pubsub_message)
            raise ValueError(f"Invalid Pub/Sub message structure: {pubsub_message}")

    except Exception as e:
        logger.error("Error extracting Pub/Sub message from CloudEvent: %s", e)
        raise ValueError(f"Invalid CloudEvent format: {e}")

    try:
        logger.info(
            "Attempting to decode base64 data: %s", raw_b64[:100] if raw_b64 else "None"
        )
        raw = base64.b64decode(raw_b64)
        logger.info("Decoded raw data: %s", raw[:200] if raw else "Empty")

        if not raw:
            logger.error("Base64 decode resulted in empty data")
            raise ValueError("Empty data after base64 decode")

        # Check if the decoded data is still base64 encoded (double encoding)
        try:
            # Try to decode as JSON first
            gmail_event = json.loads(raw)
            logger.info(
                "Successfully parsed Gmail event on first decode: %s", gmail_event
            )
        except json.JSONDecodeError:
            # If JSON parsing fails, try decoding as base64 again (double encoding case)
            logger.info("First JSON decode failed, trying double base64 decode")
            try:
                double_decoded = base64.b64decode(raw)
                logger.info(
                    "Double decoded data: %s",
                    double_decoded[:200] if double_decoded else "Empty",
                )
                gmail_event = json.loads(double_decoded)
                logger.info(
                    "Successfully parsed Gmail event after double decode: %s",
                    gmail_event,
                )
            except Exception as double_decode_error:
                logger.error("Double decode also failed: %s", double_decode_error)
                raise json.JSONDecodeError(
                    "Could not parse as JSON after single or double base64 decode",
                    raw,
                    0,
                )
    except Exception as e:
        logger.error("Decode/parse error: %s", e)
        logger.error("Raw base64 data was: %s", raw_b64)
        logger.error(
            "Decoded raw data was: %s", raw if "raw" in locals() else "Failed to decode"
        )
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
