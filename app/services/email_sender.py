"""
Email sending service using Mailgun.
📤 Handles auto-replies to customers and team forwarding.
"""

import logging
import httpx
from ..utils.config import get_config
from ..utils.email_templates import create_customer_template, create_team_template

logger = logging.getLogger(__name__)

async def send_auto_reply(email_data: dict, classification: dict, draft_response: str):
    """
    📤 Send personalized auto-reply to customer
    
    Args:
        email_data: Original email data from Mailgun webhook
        classification: AI classification result
        draft_response: AI-generated response draft
    """
    
    try:
        # Create customer-facing email content
        subject = f"Re: {email_data['subject']}"
        text_body, html_body = create_customer_template(draft_response, classification)
        
        result = await _send_email(
            to=email_data['from'],
            subject=subject,
            text=text_body,
            html=html_body,
            headers={
                "X-Auto-Reply": "true",
                "X-Classification": classification['category'],
                "In-Reply-To": email_data.get('message_id', ''),
                "References": email_data.get('message_id', '')
            }
        )
        
        logger.info(f"📨 Auto-reply sent to {email_data['from']} (ID: {result.get('id', 'unknown')})")
        
    except Exception as e:
        logger.error(f"❌ Auto-reply failed: {e}")

async def forward_to_team(email_data: dict, forward_to: str, classification: dict, draft_response: str):
    """
    📨 Forward email with AI draft to team member
    
    Args:
        email_data: Original email data from Mailgun webhook  
        forward_to: Team member email address
        classification: AI classification result
        draft_response: AI-generated response draft
    """
    
    try:
        # Create team-facing email content
        subject = f"[{classification['category'].upper()}] {email_data['subject']}"
        text_body, html_body = create_team_template(email_data, classification, draft_response)
        
        result = await _send_email(
            to=forward_to,
            subject=subject,
            text=text_body,
            html=html_body,
            headers={
                "X-Original-From": email_data['from'],
                "X-Classification": classification['category'],
                "X-Confidence": str(classification['confidence']),
                "Reply-To": email_data['from']  # Allow direct replies to customer
            }
        )
        
        logger.info(f"📨 Email forwarded to {forward_to} (ID: {result.get('id', 'unknown')})")
        
    except Exception as e:
        logger.error(f"❌ Email forwarding failed: {e}")

async def _send_email(to: str, subject: str, text: str, html: str, headers: dict = None) -> dict:
    """
    🔧 Internal email sending via Mailgun API
    
    Args:
        to: Recipient email address
        subject: Email subject
        text: Plain text body
        html: HTML body  
        headers: Optional custom headers
        
    Returns:
        Mailgun API response
    """
    
    config = get_config()
    
    # Prepare email data
    data = {
        "from": f"AI Email Router <admin@{config.mailgun_domain}>",
        "to": to,
        "subject": subject,
        "text": text,
        "html": html
    }
    
    # Add custom headers
    if headers:
        for key, value in headers.items():
            data[f"h:{key}"] = value
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.mailgun.net/v3/{config.mailgun_domain}/messages",
                auth=("api", config.mailgun_api_key),
                data=data,
                timeout=30.0
            )
            
            response.raise_for_status()
            result = response.json()
            
            logger.debug(f"📬 Mailgun response: {result}")
            return result
            
    except httpx.HTTPError as e:
        logger.error(f"❌ Mailgun API error: {e}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"Response: {e.response.text}")
        raise
    except Exception as e:
        logger.error(f"❌ Email sending failed: {e}")
        raise 