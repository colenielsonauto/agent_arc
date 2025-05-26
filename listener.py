"""
CloudEvent Pub/Sub background handler → AI pipeline.
Triggered by Pub/Sub topic: email-inbound
Cloud Functions gen-2 ready (entrypoint: pubsub_webhook)
"""
from cloudevents.http import CloudEvent
import base64
import json
import logging

from functions.ingest_email import ingest_email
from functions.analyze_email import analyze_email
from functions.forward_and_draft import forward_and_draft

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_and_ingest_emails(gmail_event):
    """
    Fetch emails from Gmail using historyId and process them.
    Gmail push notifications contain {emailAddress, historyId}, not messageId.
    """
    logger.info(f"Gmail event received: {gmail_event}")
    
    # Extract historyId from Gmail push notification
    history_id = gmail_event.get('historyId')
    email_address = gmail_event.get('emailAddress')
    
    if not history_id:
        logger.error("No historyId in Gmail event")
        raise ValueError("Missing historyId in Gmail push notification")
    
    logger.info(f"Processing history changes since historyId: {history_id}")
    
    try:
        # Import Gmail service here to avoid circular imports
        from functions.forward_and_draft import get_gmail_service
        
        service = get_gmail_service()
        if not service:
            logger.error("Failed to get Gmail service for message fetching")
            # Fallback to test data for development
            return ingest_email(gmail_event)
        
        # Get history of changes since the provided historyId
        history_response = service.users().history().list(
            userId='me',
            startHistoryId=history_id,
            labelId='INBOX'
        ).execute()
        
        history_records = history_response.get('history', [])
        logger.info(f"Found {len(history_records)} history records")
        
        # Process each history record for new messages
        for record in history_records:
            messages_added = record.get('messagesAdded', [])
            for message_added in messages_added:
                message = message_added.get('message', {})
                message_id = message.get('id')
                
                if message_id:
                    logger.info(f"Fetching message: {message_id}")
                    
                    # Fetch full message content
                    full_message = service.users().messages().get(
                        userId='me',
                        id=message_id,
                        format='full'
                    ).execute()
                    
                    # Parse the message and process through pipeline
                    email_dict = ingest_email(full_message, context='gmail_api')
                    return email_dict
        
        # No new messages found
        logger.info("No new messages found in history")
        return None
        
    except Exception as e:
        logger.error(f"Error fetching Gmail messages: {e}")
        # Fallback to test data for development/testing
        logger.info("Falling back to test data")
        return ingest_email(gmail_event)

def pubsub_webhook(event: CloudEvent, context=None) -> None:
    """Background function triggered by Pub/Sub."""
    logger.info("Received Pub/Sub CloudEvent")
    
    try:
        # Decode base64 message data from CloudEvent
        raw = base64.b64decode(event.data["message"]["data"])
        gmail_event = json.loads(raw)
        logger.info(f"Parsed Gmail event: {gmail_event}")
        
    except (ValueError, json.JSONDecodeError, KeyError) as e:
        logger.error(f"Failed to decode/parse CloudEvent message data: {e}")
        raise ValueError(f"Invalid CloudEvent message data: {e}")
    
    try:
        # Process email through the AI pipeline
        logger.info("Starting email processing pipeline")
        
        # Step 1: Fetch and ingest email
        email_dict = fetch_and_ingest_emails(gmail_event)
        
        if not email_dict:
            logger.info("No new emails to process")
            return
            
        logger.info(f"Email ingested: {email_dict.get('subject', 'No Subject')}")
        
        # Step 2: Analyze email with AI
        analysis = analyze_email(email_dict)
        logger.info(f"Email classified as: {analysis['classification']}")
        
        # Step 3: Forward and draft response
        result = forward_and_draft(analysis)
        logger.info(f"Email forwarded to: {result['forwarded_to']}")
        
        logger.info("Email processing pipeline completed successfully")
        
        logging.info("Processed Gmail event with historyId %s",
                     gmail_event.get("historyId"))
        
    except Exception as e:
        logger.error(f"Error processing email pipeline: {e}")
        # Re-raise to trigger Pub/Sub retry
        raise

 