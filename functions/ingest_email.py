import base64
import json
import email
import re
from flask import Request

def ingest_email(event, context=None):
    """
    Parse Gmail message payload into normalized email dict.
    Handles both test data (for development) and real Gmail API messages.
    
    Args:
        event: Gmail API message object or test dict
        context: Optional context ('gmail_api' for real messages)
    
    Returns:
        dict: Normalized email with 'from', 'subject', 'body' fields
    """
    
    # Handle test data (backward compatibility)
    if context != 'gmail_api' or not isinstance(event, dict) or 'payload' not in event:
        print("Using test data for email ingestion")
        normalized = {
            "from": "test@domain.com", 
            "subject": "Test",
            "body": "Hello world"
        }
        print("Ingested:", normalized)
        return normalized
    
    try:
        # Parse real Gmail API message
        payload = event.get('payload', {})
        headers = payload.get('headers', [])
        
        # Extract headers
        subject = ""
        from_addr = ""
        date = ""
        
        for header in headers:
            name = header.get('name', '').lower()
            value = header.get('value', '')
            
            if name == 'subject':
                subject = value
            elif name == 'from':
                from_addr = value
            elif name == 'date':
                date = value
        
        # Extract body content
        body = extract_message_body(payload)
        
        # Clean up from address (extract just email if in "Name <email>" format)
        from_email = extract_email_from_header(from_addr)
        
        normalized = {
            "from": from_email,
            "subject": subject,
            "body": body,
            "date": date,
            "message_id": event.get('id', ''),
            "thread_id": event.get('threadId', '')
        }
        
        print("Ingested Gmail message:", {
            "from": normalized["from"],
            "subject": normalized["subject"], 
            "body_length": len(normalized["body"])
        })
        
        return normalized
        
    except Exception as e:
        print(f"Error parsing Gmail message: {e}")
        # Fallback to test data
        normalized = {
            "from": "parse-error@domain.com",
            "subject": "Email Parse Error", 
            "body": f"Failed to parse email: {e}"
        }
        print("Ingested (error fallback):", normalized)
        return normalized

def extract_message_body(payload):
    """
    Extract text body from Gmail message payload.
    Handles multipart messages and different encodings.
    """
    body = ""
    
    # Check if single part message
    if 'body' in payload and 'data' in payload['body']:
        body = decode_base64_body(payload['body']['data'])
        return body
    
    # Handle multipart message
    parts = payload.get('parts', [])
    for part in parts:
        mime_type = part.get('mimeType', '')
        
        # Prefer text/plain, fallback to text/html
        if mime_type == 'text/plain' and 'body' in part:
            if 'data' in part['body']:
                body = decode_base64_body(part['body']['data'])
                break
        elif mime_type == 'text/html' and not body and 'body' in part:
            if 'data' in part['body']:
                html_body = decode_base64_body(part['body']['data'])
                # Strip HTML tags for plain text
                body = strip_html_tags(html_body)
        
        # Handle nested multipart
        elif mime_type.startswith('multipart/') and 'parts' in part:
            nested_body = extract_message_body(part)
            if nested_body:
                body = nested_body
                break
    
    return body.strip()

def decode_base64_body(data):
    """Decode base64url encoded body data"""
    try:
        # Gmail uses base64url encoding
        decoded = base64.urlsafe_b64decode(data + '===')  # Add padding
        return decoded.decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"Error decoding body: {e}")
        return ""

def strip_html_tags(html_text):
    """Remove HTML tags from text"""
    clean = re.compile('<.*?>')
    return re.sub(clean, '', html_text)

def extract_email_from_header(from_header):
    """Extract email address from 'From' header (handles 'Name <email>' format)"""
    if not from_header:
        return ""
    
    # Look for email in < > brackets
    email_match = re.search(r'<([^>]+)>', from_header)
    if email_match:
        return email_match.group(1)
    
    # If no brackets, assume the whole thing is an email
    # Remove any extra whitespace
    return from_header.strip() 