"""
Email sending service using Mailgun with multi-tenant support.
📤 Handles auto-replies to customers and team forwarding with client-specific branding.
"""

import logging
import httpx
from typing import Dict, Any, Optional

from ..utils.config import get_config
from ..utils.email_templates import create_customer_template, create_team_template
from ..services.client_manager import ClientManager, get_client_manager

logger = logging.getLogger(__name__)


async def send_auto_reply(email_data: Dict[str, Any], classification: Dict[str, Any], 
                         draft_response: str, client_id: Optional[str] = None):
    """
    📤 Send personalized auto-reply to customer with client-specific branding.
    
    Args:
        email_data: Original email data from Mailgun webhook
        classification: AI classification result
        draft_response: AI-generated response draft
        client_id: Optional client ID (will be identified if not provided)
    """
    try:
        # Get client manager
        client_manager = get_client_manager()
        
        # Identify client if not provided
        if not client_id:
            client_id = client_manager.identify_client_by_email(
                email_data.get('to') or email_data.get('recipient', '')
            )
        
        # Get client-specific branding and configuration
        if client_id:
            try:
                client_config = client_manager.get_client_config(client_id)
                sender_name = client_config.branding.company_name
                sender_signature = client_config.branding.email_signature
                
                # Check if auto-reply is enabled for this client
                if not client_config.settings.auto_reply_enabled:
                    logger.info(f"Auto-reply disabled for client {client_id}, skipping")
                    return
                
            except Exception as e:
                logger.warning(f"Failed to load client config for {client_id}: {e}")
                sender_name = "AI Email Router"
                sender_signature = "Support Team"
        else:
            # No client identified, use generic branding
            sender_name = "AI Email Router"
            sender_signature = "Support Team"
        
        # Create customer-facing email content
        subject = f"Re: {email_data.get('subject', 'Your inquiry')}"
        
        # Use client-specific template if available
        if client_id:
            text_body, html_body = create_client_customer_template(
                client_id, draft_response, classification, client_manager
            )
        else:
            text_body, html_body = create_customer_template(draft_response, classification)
        
        # Send email with client-specific sender
        result = await _send_email(
            to=email_data.get('from', ''),
            subject=subject,
            text=text_body,
            html=html_body,
            sender_name=sender_name,
            client_id=client_id,
            headers={
                "X-Auto-Reply": "true",
                "X-Classification": classification.get('category', 'general'),
                "X-Client-ID": client_id or "unknown",
                "In-Reply-To": email_data.get('message_id', ''),
                "References": email_data.get('message_id', '')
            }
        )
        
        logger.info(f"📨 Auto-reply sent to {email_data.get('from', '')} "
                   f"(Client: {client_id or 'unknown'}, ID: {result.get('id', 'unknown')})")
        
    except Exception as e:
        logger.error(f"❌ Auto-reply failed: {e}")


async def forward_to_team(email_data: Dict[str, Any], forward_to: str, classification: Dict[str, Any], 
                         draft_response: str, client_id: Optional[str] = None):
    """
    📨 Forward email with AI draft to team member using client-specific configuration.
    
    Args:
        email_data: Original email data from Mailgun webhook  
        forward_to: Team member email address
        classification: AI classification result
        draft_response: AI-generated response draft
        client_id: Optional client ID (will be identified if not provided)
    """
    try:
        # Get client manager
        client_manager = get_client_manager()
        
        # Identify client if not provided
        if not client_id:
            client_id = client_manager.identify_client_by_email(
                email_data.get('to') or email_data.get('recipient', '')
            )
        
        # Get client-specific branding and configuration
        if client_id:
            try:
                client_config = client_manager.get_client_config(client_id)
                sender_name = f"{client_config.branding.company_name} Email Router"
                
                # Check if team forwarding is enabled for this client
                if not client_config.settings.team_forwarding_enabled:
                    logger.info(f"Team forwarding disabled for client {client_id}, skipping")
                    return
                
            except Exception as e:
                logger.warning(f"Failed to load client config for {client_id}: {e}")
                sender_name = "AI Email Router"
        else:
            # No client identified, use generic branding
            sender_name = "AI Email Router"
        
        # Create team-facing email content
        category = classification.get('category', 'general')
        confidence = classification.get('confidence', 0.5)
        subject = f"[{category.upper()}] {email_data.get('subject', 'Email Inquiry')}"
        
        # Use client-specific template if available
        if client_id:
            text_body, html_body = create_client_team_template(
                client_id, email_data, classification, draft_response, client_manager
            )
        else:
            text_body, html_body = create_team_template(email_data, classification, draft_response)
        
        # Send email with client-specific sender
        result = await _send_email(
            to=forward_to,
            subject=subject,
            text=text_body,
            html=html_body,
            sender_name=sender_name,
            client_id=client_id,
            headers={
                "X-Original-From": email_data.get('from', ''),
                "X-Classification": category,
                "X-Confidence": str(confidence),
                "X-Client-ID": client_id or "unknown",
                "Reply-To": email_data.get('from', '')  # Allow direct replies to customer
            }
        )
        
        logger.info(f"📨 Email forwarded to {forward_to} "
                   f"(Client: {client_id or 'unknown'}, ID: {result.get('id', 'unknown')})")
        
    except Exception as e:
        logger.error(f"❌ Email forwarding failed: {e}")


def create_client_customer_template(client_id: str, draft_response: str, classification: Dict[str, Any],
                                  client_manager: ClientManager) -> tuple[str, str]:
    """
    Create customer template with client-specific branding.
    
    Args:
        client_id: Client identifier
        draft_response: AI-generated response content
        classification: Email classification result
        client_manager: ClientManager instance
        
    Returns:
        Tuple of (text_body, html_body) with client branding
    """
    try:
        client_config = client_manager.get_client_config(client_id)
        
        # Get client-specific values
        company_name = client_config.branding.company_name
        email_signature = client_config.branding.email_signature
        primary_color = client_config.branding.primary_color
        secondary_color = client_config.branding.secondary_color
        
        # Get response time for this category
        category = classification.get('category', 'general')
        response_time = client_manager.get_response_time(client_id, category)
        
        # Generate ticket ID
        ticket_id = _generate_ticket_id()
        
        # Create text version with client branding
        text_body = f"""
{draft_response}

Expected Response Time: {response_time}

Best regards,
{email_signature}

---
Ticket #: {ticket_id}
This is an automated acknowledgment from {company_name}. A team member will follow up personally.
"""
        
        # Create HTML version with client branding
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Thank You for Contacting {company_name}</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; background-color: #f8f9fa;">
    <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff;">
        
        <!-- Header with client branding -->
        <div style="background: linear-gradient(135deg, {primary_color} 0%, {secondary_color} 100%); padding: 30px; text-align: center;">
            <h1 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: 600;">Thank You for Contacting {company_name}</h1>
        </div>
        
        <!-- Main Content -->
        <div style="padding: 40px 30px;">
            <div style="background-color: #f8f9ff; border-left: 4px solid {primary_color}; padding: 20px; margin-bottom: 30px; border-radius: 0 6px 6px 0;">
                <p style="margin: 0; color: #2d3748; line-height: 1.6; font-size: 16px;">{draft_response}</p>
            </div>
            
            <div style="background-color: #f0f9ff; border: 1px solid #e0f2fe; border-radius: 8px; padding: 20px; margin-bottom: 30px;">
                <div style="display: flex; align-items: center; margin-bottom: 10px;">
                    <span style="color: #0369a1; font-size: 18px; margin-right: 8px;">⏱️</span>
                    <strong style="color: #0369a1;">Expected Response Time:</strong>
                </div>
                <p style="margin: 0; color: #075985; font-size: 16px; font-weight: 600;">{response_time}</p>
            </div>
            
            <div style="text-align: center; color: #64748b; font-size: 14px; line-height: 1.5;">
                <p>Ticket #: <strong>{ticket_id}</strong></p>
                <p>Best regards,<br><strong>{email_signature}</strong></p>
            </div>
        </div>
        
        <!-- Footer -->
        <div style="background-color: #f8f9fa; padding: 20px 30px; text-align: center; border-top: 1px solid #e2e8f0;">
            <p style="margin: 0; color: #64748b; font-size: 12px;">
                🤖 This is an automated acknowledgment from {company_name}. A team member will follow up personally.
            </p>
        </div>
        
    </div>
</body>
</html>
"""
        
        return text_body, html_body
        
    except Exception as e:
        logger.error(f"Failed to create client-specific customer template for {client_id}: {e}")
        # Fall back to generic template
        return create_customer_template(draft_response, classification)


def create_client_team_template(client_id: str, email_data: Dict[str, Any], classification: Dict[str, Any],
                               draft_response: str, client_manager: ClientManager) -> tuple[str, str]:
    """
    Create team template with client-specific context.
    
    Args:
        client_id: Client identifier
        email_data: Original email data
        classification: Email classification result
        draft_response: AI-generated analysis
        client_manager: ClientManager instance
        
    Returns:
        Tuple of (text_body, html_body) with client context
    """
    try:
        client_config = client_manager.get_client_config(client_id)
        
        # Get client-specific values
        company_name = client_config.branding.company_name
        category = classification.get('category', 'general')
        confidence = classification.get('confidence', 0.0)
        reasoning = classification.get('reasoning', 'No reasoning provided')
        
        # Get routing destination
        routing_destination = client_manager.get_routing_destination(client_id, category)
        
        # Create text version with client context
        text_body = f"""
🤖 {company_name} EMAIL ROUTER - FORWARDED MESSAGE

📋 CLASSIFICATION: {category} (confidence: {confidence:.2f})
💭 REASONING: {reasoning}
🎯 CLIENT: {company_name} ({client_id})

📧 ORIGINAL MESSAGE:
From: {email_data.get('from', '')}
To: {email_data.get('to', '')}
Subject: {email_data.get('subject', '')}

{email_data.get('stripped_text') or email_data.get('body_text', '')}

---

✍️ AI ANALYSIS:

{draft_response}

---
Reply to this email to respond to the original sender.
The customer has already received an automated acknowledgment.
Routing destination: {routing_destination}
"""
        
        # Create enhanced HTML with client context
        analysis_html = draft_response.replace('\n', '<br>')
        email_body_html = (email_data.get('stripped_text') or email_data.get('body_text', '')).replace('\n', '<br>')
        
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{company_name} Email Analysis</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; background-color: #f8f9fa;">
    <div style="max-width: 800px; margin: 0 auto; background-color: #ffffff;">
        
        <!-- Header -->
        <div style="background: linear-gradient(135deg, #1e293b 0%, #334155 100%); padding: 25px; color: white;">
            <h1 style="margin: 0; font-size: 22px; font-weight: 600;">🤖 {company_name} Email Analysis</h1>
            <p style="margin: 8px 0 0 0; opacity: 0.9; font-size: 14px;">Client: {client_id}</p>
        </div>
        
        <!-- Classification Card -->
        <div style="margin: 20px; background: linear-gradient(135deg, #ecfdf5 0%, #f0fdf4 100%); border: 1px solid #bbf7d0; border-radius: 12px; padding: 20px;">
            <div style="margin-bottom: 15px;">
                <span style="font-size: 24px; margin-right: 10px;">📋</span>
                <span style="color: #166534; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; font-size: 18px;">{category}</span>
                <span style="margin-left: 15px; background: #16a34a; color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600;">{confidence:.0%} CONFIDENT</span>
            </div>
            <p style="margin: 0; color: #166534; font-weight: 500;">{reasoning}</p>
        </div>
        
        <!-- Original Email Card -->
        <div style="margin: 20px; border: 1px solid #e5e7eb; border-radius: 12px; overflow: hidden;">
            <div style="background: #f9fafb; padding: 15px; border-bottom: 1px solid #e5e7eb;">
                <h3 style="margin: 0; color: #374151; font-size: 16px;">📧 Original Message</h3>
            </div>
            <div style="padding: 20px;">
                <div style="margin-bottom: 15px;">
                    <strong style="color: #374151;">From:</strong> <span style="color: #6b7280;">{email_data.get('from', '')}</span><br>
                    <strong style="color: #374151;">Subject:</strong> <span style="color: #6b7280;">{email_data.get('subject', '')}</span>
                </div>
                <div style="background: #f8fafc; border-left: 4px solid #3b82f6; padding: 15px; border-radius: 0 6px 6px 0;">
                    <p style="margin: 0; color: #1e293b; line-height: 1.6;">{email_body_html}</p>
                </div>
            </div>
        </div>
        
        <!-- AI Analysis Card -->
        <div style="margin: 20px; border: 1px solid #e5e7eb; border-radius: 12px; overflow: hidden;">
            <div style="background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%); padding: 15px; border-bottom: 1px solid #93c5fd;">
                <h3 style="margin: 0; color: #1e40af; font-size: 16px;">🔍 AI Analysis & Recommendations</h3>
            </div>
            <div style="padding: 20px;">
                <div style="color: #1e293b; line-height: 1.7;">{analysis_html}</div>
            </div>
        </div>
        
        <!-- Action Buttons -->
        <div style="margin: 20px; text-align: center; padding: 20px;">
            <p style="color: #6b7280; margin-bottom: 15px; font-size: 14px;">
                ✅ Customer has already received an automated acknowledgment
            </p>
            <div style="background: #f0f9ff; border: 1px solid #c7d2fe; border-radius: 8px; padding: 15px; margin-top: 20px;">
                <p style="margin: 0; color: #3730a3; font-weight: 600;">
                    📧 Reply to this email to respond directly to the customer
                </p>
                <p style="margin: 5px 0 0 0; color: #6366f1; font-size: 14px;">
                    Routed to: {routing_destination}
                </p>
            </div>
        </div>
        
    </div>
</body>
</html>
"""
        
        return text_body, html_body
        
    except Exception as e:
        logger.error(f"Failed to create client-specific team template for {client_id}: {e}")
        # Fall back to generic template
        return create_team_template(email_data, classification, draft_response)


async def _send_email(to: str, subject: str, text: str, html: str, sender_name: str = "AI Email Router",
                     client_id: Optional[str] = None, headers: Dict[str, str] = None) -> Dict[str, Any]:
    """
    🔧 Internal email sending via Mailgun API with client-specific sender.
    
    Args:
        to: Recipient email address
        subject: Email subject
        text: Plain text body
        html: HTML body
        sender_name: Sender name for branding
        client_id: Optional client ID for tracking
        headers: Optional custom headers
        
    Returns:
        Mailgun API response
    """
    config = get_config()
    
    # Prepare email data with client-specific sender
    data = {
        "from": f"{sender_name} <admin@{config.mailgun_domain}>",
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


def _generate_ticket_id() -> str:
    """Generate a simple ticket ID"""
    import random
    import string
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8)) 