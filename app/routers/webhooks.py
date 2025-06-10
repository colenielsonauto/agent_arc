"""
Webhook handlers for incoming emails with multi-tenant support.
🎯 CORE MVP ENDPOINT: /webhooks/mailgun/inbound
"""

import logging
from fastapi import APIRouter, Request, BackgroundTasks, Depends
from typing import Optional

from ..services.dynamic_classifier import DynamicClassifier, get_dynamic_classifier
from ..services.client_manager import ClientManager, get_client_manager
from ..services.routing_engine import RoutingEngine, get_routing_engine
from ..services.email_composer import generate_customer_acknowledgment, generate_team_analysis
from ..services.email_sender import send_auto_reply, forward_to_team

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/mailgun/inbound")
async def mailgun_inbound_webhook(
    request: Request, 
    background_tasks: BackgroundTasks,
    client_manager = Depends(get_client_manager),
    dynamic_classifier = Depends(get_dynamic_classifier),
    routing_engine = Depends(get_routing_engine)
):
    """
    🎯 CORE MVP ENDPOINT: Receive inbound emails from Mailgun with multi-tenant support
    
    Flow:
    1. Mailgun → /webhooks/mailgun/inbound  
    2. Identify client from recipient domain
    3. Classify email with client-specific Claude prompts
    4. Route to appropriate team member using client rules
    5. Generate personalized auto-reply with client branding
    6. Send auto-reply to customer
    7. Forward with analysis to team member
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
            "message_id": form_data.get("Message-Id", ""),
        }
        
        logger.info(f"📧 Received email from {email_data['from']}: {email_data['subject']}")
        
        # Identify client from recipient domain
        identification_result = client_manager.identify_client_by_email(email_data['to'])
        client_id = identification_result.client_id if identification_result.is_successful else None
        
        if client_id:
            logger.info(f"🎯 Identified client: {client_id} (confidence: {identification_result.confidence:.2f}, method: {identification_result.method})")
        else:
            logger.warning(f"⚠️ No client identified for recipient: {email_data['to']}")
        
        # Process email in background (non-blocking)
        background_tasks.add_task(
            process_email_pipeline, 
            email_data, 
            client_id,
            dynamic_classifier,
            client_manager,
            routing_engine
        )
        
        return {"status": "received", "message": "Email processing started", "client_id": client_id}
        
    except Exception as e:
        logger.error(f"❌ Webhook processing failed: {e}")
        return {"status": "error", "message": str(e)}


async def process_email_pipeline(email_data: dict, client_id: Optional[str],
                               dynamic_classifier,
                               client_manager,
                               routing_engine):
    """
    🔄 Background task: Complete multi-tenant email processing pipeline
    """
    try:
        logger.info(f"🤖 Processing email for client {client_id or 'unknown'}: {email_data['subject']}")
        
        # Step 1: AI Classification with client-specific prompts
        classification = await dynamic_classifier.classify_email(email_data, client_id)
        
        category = classification.get('category', 'general')
        confidence = classification.get('confidence', 0.0)
        method = classification.get('method', 'unknown')
        
        logger.info(f"📋 Classification: {category} ({confidence:.2f}, {method})")
        
        # Step 2: Routing with client-specific rules
        if client_id:
            routing_result = routing_engine.route_email(client_id, classification, email_data)
            forward_to = routing_result['primary_destination']
            
            logger.info(f"📍 Routing: {category} → {forward_to}")
            
            # Log special handling if any
            special_handling = routing_result.get('special_handling', [])
            if special_handling:
                logger.info(f"🚨 Special handling: {', '.join(special_handling)}")
        else:
            # Fallback routing when no client identified
            forward_to = "admin@example.com"  # TODO: Make this configurable
            logger.warning("Using fallback routing for unknown client")
        
        # Step 3: Generate customer acknowledgment with client branding
        customer_acknowledgment = await generate_customer_acknowledgment(
            email_data, classification, client_id
        )
        
        # Step 4: Generate team analysis with client context
        team_analysis = await generate_team_analysis(
            email_data, classification, client_id
        )
        
        # Step 5: Send customer acknowledgment with client branding
        await send_auto_reply(email_data, classification, customer_acknowledgment, client_id)
        
        # Step 6: Forward to team with detailed analysis
        await forward_to_team(email_data, forward_to, classification, team_analysis, client_id)
        
        # Log successful completion
        if client_id:
            client_config = client_manager.get_client_config(client_id)
            company_name = client_config.branding.company_name
            logger.info(f"✅ Email processed for {company_name}: "
                       f"acknowledgment sent + analysis forwarded to {forward_to}")
        else:
            logger.info(f"✅ Email processed (no client): "
                       f"acknowledgment sent + analysis forwarded to {forward_to}")
        
    except Exception as e:
        logger.error(f"❌ Email pipeline failed: {e}")
        
        # Try to send a basic notification about the failure
        try:
            if client_id:
                client_config = client_manager.get_client_config(client_id)
                admin_email = client_config.contacts.primary_contact
            else:
                admin_email = "admin@example.com"  # TODO: Make this configurable
            
            await _send_failure_notification(email_data, str(e), admin_email)
            
        except Exception as notification_error:
            logger.error(f"❌ Failed to send failure notification: {notification_error}")


async def _send_failure_notification(email_data: dict, error_message: str, admin_email: str):
    """
    Send notification about email processing failure.
    
    Args:
        email_data: Original email data
        error_message: Error that occurred
        admin_email: Admin email to notify
    """
    try:
        failure_classification = {
            'category': 'general',
            'confidence': 0.0,
            'reasoning': 'Email processing failed',
            'method': 'failure_notification'
        }
        
        failure_message = f"""
Email processing failed with error: {error_message}

Original email:
From: {email_data.get('from', '')}
Subject: {email_data.get('subject', '')}
Body: {email_data.get('stripped_text') or email_data.get('body_text', '')[:200]}...

Please review this email manually.
"""
        
        await forward_to_team(
            email_data, 
            admin_email, 
            failure_classification, 
            failure_message
        )
        
        logger.info(f"📧 Failure notification sent to {admin_email}")
        
    except Exception as e:
        logger.error(f"Failed to send failure notification: {e}")


@router.get("/status")
async def webhook_status(client_manager = Depends(get_client_manager)):
    """
    Get webhook processing status and client information.
    
    Returns:
        Status information including available clients
    """
    try:
        available_clients = client_manager.get_available_clients()
        
        # Get client details
        client_details = []
        for client_id in available_clients:
            try:
                client_config = client_manager.get_client_config(client_id)
                client_details.append({
                    'id': client_id,
                    'name': client_config.client.name,
                    'industry': client_config.client.industry,
                    'status': client_config.client.status,
                    'domains': {
                        'primary': client_config.domains.primary,
                        'support': client_config.domains.support
                    },
                    'settings': {
                        'auto_reply_enabled': client_config.settings.auto_reply_enabled,
                        'ai_classification_enabled': client_config.settings.ai_classification_enabled
                    }
                })
            except Exception as e:
                logger.warning(f"Failed to load details for client {client_id}: {e}")
                client_details.append({
                    'id': client_id,
                    'error': str(e)
                })
        
        return {
            "status": "active",
            "webhook_endpoint": "/webhooks/mailgun/inbound",
            "total_clients": len(available_clients),
            "clients": client_details
        }
        
    except Exception as e:
        logger.error(f"Failed to get webhook status: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/test")
async def test_webhook(request: Request, background_tasks: BackgroundTasks,
                      client_manager = Depends(get_client_manager),
                      dynamic_classifier = Depends(get_dynamic_classifier),
                      routing_engine = Depends(get_routing_engine)):
    """
    Test endpoint for webhook functionality.
    
    Accepts JSON payload with test email data.
    """
    try:
        # Get JSON data instead of form data for testing
        test_data = await request.json()
        
        # Convert to expected format
        email_data = {
            "from": test_data.get("from", "test@example.com"),
            "to": test_data.get("to", "support@colenielson.dev"),
            "subject": test_data.get("subject", "Test Email"),
            "body_text": test_data.get("body", "This is a test email."),
            "body_html": "",
            "stripped_text": test_data.get("body", "This is a test email."),
            "timestamp": "",
            "message_id": "test-message-id",
        }
        
        logger.info(f"🧪 Test email from {email_data['from']}: {email_data['subject']}")
        
        # Identify client
        identification_result = client_manager.identify_client_by_email(email_data['to'])
        client_id = identification_result.client_id if identification_result.is_successful else None
        
        # Process in background
        background_tasks.add_task(
            process_email_pipeline, 
            email_data, 
            client_id,
            dynamic_classifier,
            client_manager,
            routing_engine
        )
        
        return {
            "status": "test_received", 
            "message": "Test email processing started",
            "client_id": client_id,
            "email_data": email_data
        }
        
    except Exception as e:
        logger.error(f"❌ Test webhook failed: {e}")
        return {"status": "error", "message": str(e)} 