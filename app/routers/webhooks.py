"""
Webhook handlers for incoming emails.
🎯 CORE MVP ENDPOINT: /webhooks/mailgun/inbound
"""

import logging
from fastapi import APIRouter, Request, BackgroundTasks
from ..services.classifier import classify_email
from ..services.email_composer import generate_customer_acknowledgment, generate_team_analysis
from ..services.email_sender import send_auto_reply, forward_to_team
from ..utils.config import get_config

logger = logging.getLogger(__name__)
router = APIRouter()

# Routing rules - TODO: Move to environment variables
ROUTING_RULES = {
    "support": "colenielson.re@gmail.com",
    "billing": "colenielson8@gmail.com", 
    "sales": "colenielson@u.boisestate.edu",
    "technical": "colenielson.re@gmail.com",
    "complaint": "colenielson8@gmail.com",
    "general": "colenielson.re@gmail.com"
}

@router.post("/mailgun/inbound")
async def mailgun_inbound_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    🎯 CORE MVP ENDPOINT: Receive inbound emails from Mailgun
    
    Flow:
    1. Mailgun → /webhooks/mailgun/inbound  
    2. Classify email with Claude 3.5 Sonnet
    3. Generate personalized auto-reply
    4. Send auto-reply to customer
    5. Forward with draft to appropriate team member
    """
    try:
        # Extract email data from Mailgun webhook
        form_data = await request.form()
        
        email_data = {
            "from": form_data.get("from", "unknown@domain.com"),
            "to": form_data.get("recipient", ""),
            "subject": form_data.get("subject", "No Subject"),
            "body_text": form_data.get("body-plain", ""),
            "body_html": form_data.get("body-html", ""),
            "stripped_text": form_data.get("stripped-text", ""),
            "timestamp": form_data.get("timestamp", ""),
        }
        
        logger.info(f"📧 Received email from {email_data['from']}: {email_data['subject']}")
        
        # Process email in background (non-blocking)
        background_tasks.add_task(process_email_pipeline, email_data)
        
        return {"status": "received", "message": "Email processing started"}
        
    except Exception as e:
        logger.error(f"❌ Webhook processing failed: {e}")
        return {"status": "error", "message": str(e)}

async def process_email_pipeline(email_data: dict):
    """
    🔄 Background task: Complete email processing pipeline
    """
    try:
        logger.info(f"🤖 Processing email: {email_data['subject']}")
        
        # Step 1: AI Classification
        classification = await classify_email(
            subject=email_data['subject'],
            body=email_data['stripped_text'] or email_data['body_text'],
            sender=email_data['from']
        )
        
        logger.info(f"📋 Classification: {classification['category']} ({classification['confidence']:.2f})")
        
        # Step 2: Determine routing
        forward_to = ROUTING_RULES.get(classification['category'], ROUTING_RULES['general'])
        
        # Step 3: Generate SEPARATE responses
        # Customer gets brief acknowledgment
        customer_acknowledgment = await generate_customer_acknowledgment(email_data, classification)
        
        # Team gets detailed analysis
        team_analysis = await generate_team_analysis(email_data, classification)
        
        # Step 4: Send brief acknowledgment to customer
        await send_auto_reply(email_data, classification, customer_acknowledgment)
        
        # Step 5: Forward to team with detailed analysis
        await forward_to_team(email_data, forward_to, classification, team_analysis)
        
        logger.info(f"✅ Email processed: acknowledgment sent + detailed analysis forwarded to {forward_to}")
        
    except Exception as e:
        logger.error(f"❌ Email pipeline failed: {e}") 