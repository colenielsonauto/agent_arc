#!/usr/bin/env python3
"""
FastAPI application for the AI Email Router system.
Provides AI-powered email classification, auto-reply, and smart routing.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
import sys
from pathlib import Path

# Add the AI module path for direct import
ai_path = Path(__file__).parent.parent / "core" / "ai"
sys.path.insert(0, str(ai_path))

from ai_classifier import AIEmailClassifier

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
ROUTING_RULES = {
    "support": "colenielson.re@gmail.com",
    "billing": "colenielson8@gmail.com", 
    "sales": "colenielson@u.boisestate.edu",
    "technical": "colenielson.re@gmail.com",
    "complaint": "colenielson8@gmail.com",
    "general": "colenielson.re@gmail.com"
}

# Create FastAPI app
app = FastAPI(
    title="AI Email Router",
    description="AI-powered email classification and routing system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class EmailClassificationRequest(BaseModel):
    """Request model for email classification."""
    subject: str
    body: str
    sender: Optional[str] = None
    timestamp: Optional[datetime] = None

class EmailClassificationResponse(BaseModel):
    """Response model for email classification."""
    category: str
    confidence: float
    reasoning: str
    suggested_actions: List[str]
    processing_time_ms: float

class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: datetime
    version: str
    components: Dict[str, str]

# Routes
@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint."""
    return {
        "message": "AI Email Router API",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Basic health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="1.0.0",
        components={
            "api": "healthy",
            "database": "not_configured",
            "llm": "configured",
            "email": "configured"
        }
    )

@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with component status."""
    try:
        # Test AI classifier
        ai_status = "not_configured"
        try:
            classifier = AIEmailClassifier()
            ai_status = "configured"
        except Exception as e:
            logger.error(f"AI classifier initialization failed: {e}")
            ai_status = f"error: {str(e)}"
        
        components = {
            "anthropic": ai_status,
            "mailgun": "configured",
            "gmail": "not_configured"
        }
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "components": components,
            "uptime_seconds": 0,
            "environment": "development"
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")

@app.post("/classify", response_model=EmailClassificationResponse)
async def classify_email(request: EmailClassificationRequest):
    """Classify an email using AI."""
    try:
        start_time = datetime.utcnow()
        
        # Use AI classifier with fallback
        try:
            classifier = AIEmailClassifier()
            result = await classifier.classify_email(
                subject=request.subject,
                body=request.body,
                sender=request.sender
            )
            
            end_time = datetime.utcnow()
            processing_time = (end_time - start_time).total_seconds() * 1000
            
            logger.info(f"Email classified: {result['category']} ({result['confidence']})")
            
            return EmailClassificationResponse(
                category=result['category'],
                confidence=result['confidence'],
                reasoning=result['reasoning'],
                suggested_actions=result['suggested_actions'],
                processing_time_ms=processing_time
            )
            
        except Exception as ai_error:
            logger.warning(f"AI classification failed, using fallback: {ai_error}")
            
            # Simple fallback classification
            category, confidence = classify_fallback(request.subject)
            
            end_time = datetime.utcnow()
            processing_time = (end_time - start_time).total_seconds() * 1000
            
            return EmailClassificationResponse(
                category=category,
                confidence=confidence,
                reasoning="Fallback classification based on keywords",
                suggested_actions=["manual_review"],
                processing_time_ms=processing_time
            )
        
    except Exception as e:
        logger.error(f"Email classification failed: {e}")
        raise HTTPException(status_code=500, detail="Classification failed")

@app.post("/webhooks/mailgun/inbound")
async def mailgun_inbound_webhook(request: Request, background_tasks: BackgroundTasks):
    """Webhook endpoint for receiving inbound emails from Mailgun."""
    try:
        # Get the raw form data from Mailgun
        form_data = await request.form()
        
        # Extract email data from Mailgun webhook
        email_data = {
            "from": form_data.get("from", "unknown@domain.com"),
            "to": form_data.get("recipient", ""),
            "subject": form_data.get("subject", "No Subject"),
            "body_text": form_data.get("body-plain", ""),
            "body_html": form_data.get("body-html", ""),
            "timestamp": form_data.get("timestamp", ""),
            "sender": form_data.get("sender", ""),
            "stripped_text": form_data.get("stripped-text", ""),
            "message_headers": form_data.get("message-headers", ""),
        }
        
        logger.info(f"Received inbound email from {email_data['from']}: {email_data['subject']}")
        
        # Process email in background
        background_tasks.add_task(process_inbound_email, email_data)
        
        return {"status": "received", "message": "Email processing started"}
        
    except Exception as e:
        logger.error(f"Inbound webhook processing failed: {e}")
        return {"status": "error", "message": str(e)}

# Helper functions
def classify_fallback(subject: str) -> tuple[str, float]:
    """Simple fallback classification based on keywords."""
    subject_lower = subject.lower()
    
    if "billing" in subject_lower or "invoice" in subject_lower:
        return "billing", 0.85
    elif "support" in subject_lower or "help" in subject_lower:
        return "support", 0.90
    elif "sales" in subject_lower or "pricing" in subject_lower:
        return "sales", 0.80
    else:
        return "general", 0.60

async def get_email_config():
    """Get email configuration with settings reload."""
    from src.infrastructure.config.settings import reload_settings
    from src.adapters.email.mailgun import MailgunAdapter
    from src.core.interfaces.email_provider import EmailProviderConfig, EmailProvider
    
    settings = reload_settings()
    email_config = settings.get_email_config("mailgun")
    
    config = EmailProviderConfig(
        provider=EmailProvider.MAILGUN,
        credentials=email_config["credentials"],
        polling_interval=60,
        batch_size=50,
    )
    
    adapter = MailgunAdapter(config)
    await adapter.connect()
    return adapter

def create_customer_email_template(draft_response: str, classification: dict) -> tuple[str, str]:
    """Create customer-facing email templates (text and HTML)."""
    # Plain text version
    text_body = f"""
Thank you for contacting our support team!

{draft_response}

We have received your message and our team is already working on your {classification['category']} inquiry. You can expect a detailed response from one of our specialists soon.

If you have any urgent questions, please don't hesitate to reach out.

Best regards,
Customer Support Team
Cole's Portfolio Support

---
This is an automated response. Our team has been notified and will follow up personally.
"""

    # HTML version  
    draft_html = draft_response.replace('\n', '<br>')
    html_body = f"""
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; color: #333;">
    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #007bff;">
        <h3 style="color: #007bff; margin: 0;">Thank you for contacting our support team!</h3>
    </div>
    
    <div style="background-color: white; padding: 20px; border-radius: 6px; margin-bottom: 20px; border: 1px solid #e9ecef;">
        {draft_html}
    </div>
    
    <div style="background-color: #e8f5e8; padding: 15px; border-radius: 6px; margin-bottom: 20px;">
        <p style="margin: 0;"><strong>Status Update:</strong> We have received your message and our team is already working on your <strong>{classification['category']}</strong> inquiry. You can expect a detailed response from one of our specialists soon.</p>
    </div>
    
    <div style="background-color: #fff3cd; padding: 15px; border-radius: 6px; margin-bottom: 20px;">
        <p style="margin: 0;"><strong>Need immediate assistance?</strong> If you have any urgent questions, please don't hesitate to reach out.</p>
    </div>
    
    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 6px; text-align: center; border-top: 3px solid #007bff;">
        <p style="margin: 0; font-weight: bold; color: #007bff;">Best regards,<br>Customer Support Team<br>Cole's Portfolio Support</p>
        <p style="margin: 10px 0 0 0; font-size: 12px; color: #6c757d;">This is an automated response. Our team has been notified and will follow up personally.</p>
    </div>
</div>
"""
    
    return text_body, html_body

def create_team_email_template(original_email: dict, classification: dict, draft_response: str) -> tuple[str, str]:
    """Create team-facing email templates (text and HTML)."""
    # Plain text version
    text_body = f"""
AI EMAIL ROUTER - FORWARDED MESSAGE

CLASSIFICATION: {classification['category']} (confidence: {classification['confidence']:.2f})
REASONING: {classification['reasoning']}

ORIGINAL MESSAGE:
From: {original_email['from']}
To: {original_email['to']}
Subject: {original_email['subject']}

{original_email['stripped_text'] or original_email['body_text']}

---

SUGGESTED RESPONSE DRAFT:

{draft_response}

---
This message was automatically classified and routed by the AI Email Router system.
Reply to this email to respond to the original sender.
"""

    # HTML version
    draft_html = draft_response.replace('\n', '<br>')
    html_body = f"""
<div style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto;">
    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
        <h2 style="color: #2c3e50; margin: 0;">AI EMAIL ROUTER - FORWARDED MESSAGE</h2>
    </div>
    
    <div style="background-color: #e8f5e8; padding: 15px; border-radius: 6px; margin-bottom: 20px;">
        <p><strong>CLASSIFICATION:</strong> <span style="color: #27ae60; font-weight: bold;">{classification['category']}</span> (confidence: <strong>{classification['confidence']:.2f}</strong>)</p>
        <p><strong>REASONING:</strong> {classification['reasoning']}</p>
    </div>
    
    <div style="background-color: #fff3cd; padding: 15px; border-radius: 6px; margin-bottom: 20px;">
        <h3 style="color: #856404; margin-top: 0;">ORIGINAL MESSAGE:</h3>
        <p><strong>From:</strong> {original_email['from']}</p>
        <p><strong>To:</strong> {original_email['to']}</p>
        <p><strong>Subject:</strong> {original_email['subject']}</p>
        <div style="background-color: white; padding: 15px; border-left: 4px solid #ffc107; margin-top: 10px;">
            <p>{original_email['stripped_text'] or original_email['body_text']}</p>
        </div>
    </div>
    
    <hr style="border: none; border-top: 2px solid #dee2e6; margin: 30px 0;">
    
    <div style="background-color: #d1ecf1; padding: 15px; border-radius: 6px; margin-bottom: 20px;">
        <h3 style="color: #0c5460; margin-top: 0;">SUGGESTED RESPONSE DRAFT:</h3>
        <div style="background-color: white; padding: 15px; border-left: 4px solid #17a2b8; margin-top: 10px;">
            {draft_html}
        </div>
    </div>
    
    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 6px; text-align: center; color: #6c757d; font-size: 12px;">
        <p><strong>This message was automatically classified and routed by the AI Email Router system.</strong><br>
        Reply to this email to respond to the original sender.</p>
    </div>
</div>
"""
    
    return text_body, html_body

# Core processing functions
async def process_inbound_email(email_data: dict):
    """Background task to process incoming email through AI classification and routing."""
    try:
        logger.info(f"Processing email: {email_data['subject']}")
        
        # Step 1: Classify the email using AI
        classifier = AIEmailClassifier()
        classification_result = await classifier.classify_email(
            subject=email_data['subject'],
            body=email_data['stripped_text'] or email_data['body_text'],
            sender=email_data['from']
        )
        
        logger.info(f"Classification: {classification_result['category']} ({classification_result['confidence']})")
        
        # Step 2: Determine routing based on classification
        category = classification_result['category']
        forward_to = ROUTING_RULES.get(category, ROUTING_RULES['general'])
        
        # Step 3: Generate AI response draft
        draft_response = await generate_response_draft(email_data, classification_result)
        
        # Step 4: Send auto-reply to the customer
        auto_reply_result = await send_auto_reply_to_customer(
            original_email=email_data,
            classification=classification_result,
            draft_response=draft_response
        )
        
        # Step 5: Forward email with draft response to team
        forwarding_result = await forward_email_with_draft(
            original_email=email_data,
            forward_to=forward_to,
            classification=classification_result,
            draft_response=draft_response
        )
        
        logger.info(f"Email processed successfully: Auto-replied to customer and forwarded to {forward_to}")
        
    except Exception as e:
        logger.error(f"Error processing inbound email: {e}")

async def generate_response_draft(email_data: dict, classification: dict) -> str:
    """Generate a draft response using AI."""
    try:
        classifier = AIEmailClassifier()
        
        prompt = f"""
You are a professional customer service assistant. Generate a helpful draft response for this customer email.

Original Email:
From: {email_data['from']}
Subject: {email_data['subject']}
Message: {email_data['stripped_text'] or email_data['body_text']}

Classification: {classification['category']} (confidence: {classification['confidence']})
Reasoning: {classification['reasoning']}

Generate a professional, helpful draft response that:
1. Acknowledges their message
2. Shows understanding of their {classification['category']} inquiry
3. Provides next steps or helpful information
4. Maintains a professional but friendly tone

Keep the response concise but helpful. End with a professional closing.

Draft Response:
"""
        
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{classifier.base_url}/v1/messages",
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": classifier.api_key,
                    "anthropic-version": "2023-06-01"
                },
                json={
                    "model": classifier.model,
                    "max_tokens": 500,
                    "temperature": 0.7,
                    "messages": [{"role": "user", "content": prompt}]
                },
                timeout=30.0
            )
            
            response.raise_for_status()
            result = response.json()
            
            return result["content"][0]["text"].strip()
        
    except Exception as e:
        logger.error(f"Error generating response draft: {e}")
        return f"Thank you for your message regarding {classification['category']}. We have received your inquiry and will respond within 24 hours."

async def send_auto_reply_to_customer(original_email: dict, classification: dict, draft_response: str) -> dict:
    """Send an automatic personalized reply back to the original customer."""
    try:
        from src.core.interfaces.email_provider import EmailAddress
        
        adapter = await get_email_config()
        
        # Create customer-facing subject line
        customer_subject = f"Re: {original_email['subject']}"
        
        # Get email templates
        text_body, html_body = create_customer_email_template(draft_response, classification)
        
        # Send auto-reply to customer
        message_id = await adapter.send_email(
            to=[EmailAddress(email=original_email['from'])],
            subject=customer_subject,
            body_text=text_body,
            body_html=html_body,
            reply_to_id=None,
            headers={
                "X-Auto-Reply": "true",
                "X-Classification": classification['category'],
                "In-Reply-To": original_email.get('message_id', ''),
                "References": original_email.get('message_id', '')
            }
        )
        
        await adapter.disconnect()
        
        logger.info(f"Auto-reply sent to customer: {original_email['from']}")
        
        return {
            "status": "success", 
            "message_id": message_id,
            "sent_to": original_email['from'],
            "type": "auto_reply"
        }
        
    except Exception as e:
        logger.error(f"Error sending auto-reply to customer: {e}")
        return {"status": "error", "error": str(e)}

async def forward_email_with_draft(original_email: dict, forward_to: str, classification: dict, draft_response: str) -> dict:
    """Forward the original email with AI-generated draft response."""
    try:
        from src.core.interfaces.email_provider import EmailAddress
        
        adapter = await get_email_config()
        
        # Create forwarded email content
        forwarded_subject = f"[{classification['category'].upper()}] {original_email['subject']}"
        
        # Get email templates
        text_body, html_body = create_team_email_template(original_email, classification, draft_response)
        
        # Send the forwarded email with both text and HTML versions
        message_id = await adapter.send_email(
            to=[EmailAddress(email=forward_to)],
            subject=forwarded_subject,
            body_text=text_body,
            body_html=html_body,
            reply_to_id=None,
            headers={
                "X-Original-From": original_email['from'],
                "X-Classification": classification['category'],
                "X-Confidence": str(classification['confidence'])
            }
        )
        
        await adapter.disconnect()
        
        return {
            "status": "success",
            "message_id": message_id,
            "forwarded_to": forward_to,
            "classification": classification['category']
        }
        
    except Exception as e:
        logger.error(f"Error forwarding email: {e}")
        return {"status": "error", "error": str(e)}

@app.get("/status")
async def get_system_status():
    """Get current system status and statistics."""
    return {
        "system": "AI Email Router",
        "status": "operational",
        "version": "1.0.0",
        "features": {
            "email_classification": "ai_powered",
            "auto_reply": "enabled",
            "smart_routing": "enabled",
            "html_formatting": "enabled"
        }
    }

# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "type": "server_error"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 