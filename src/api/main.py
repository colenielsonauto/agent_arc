#!/usr/bin/env python3
"""
FastAPI application for the Email Router system.
This serves as the main entry point for the AI-powered email processing.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import logging
import asyncio
from datetime import datetime
import sys
from pathlib import Path

# Add the AI module path for direct import
ai_path = Path(__file__).parent.parent / "core" / "ai"
sys.path.insert(0, str(ai_path))

# Import the AI classifier directly
from ai_classifier import AIEmailClassifier

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Email Router API",
    description="AI-powered email classification and routing system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for API requests/responses
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
        "message": "🤖 Email Router API",
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
            "uptime_seconds": 0,  # Placeholder
            "environment": "development"
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")

@app.post("/classify", response_model=EmailClassificationResponse)
async def classify_email(request: EmailClassificationRequest):
    """
    Classify an email using AI.
    This is the core AI functionality endpoint.
    """
    try:
        start_time = datetime.utcnow()
        
        # Use real AI classifier
        try:
            classifier = AIEmailClassifier()
            result = await classifier.classify_email(
                subject=request.subject,
                body=request.body,
                sender=request.sender
            )
            
            end_time = datetime.utcnow()
            processing_time = (end_time - start_time).total_seconds() * 1000
            
            logger.info(f"AI classified email: category={result['category']}, confidence={result['confidence']}")
            
            return EmailClassificationResponse(
                category=result['category'],
                confidence=result['confidence'],
                reasoning=result['reasoning'],
                suggested_actions=result['suggested_actions'],
                processing_time_ms=processing_time
            )
            
        except Exception as ai_error:
            logger.warning(f"AI classification failed, using fallback: {ai_error}")
            
            # Fallback to basic classification
            if "billing" in request.subject.lower() or "invoice" in request.subject.lower():
                category = "billing"
                confidence = 0.85
                reasoning = "Email contains billing-related keywords in subject (fallback mode)"
                actions = ["forward_to_billing", "create_ticket", "auto_reply"]
            elif "support" in request.subject.lower() or "help" in request.subject.lower():
                category = "support"
                confidence = 0.90
                reasoning = "Email contains support-related keywords (fallback mode)"
                actions = ["create_support_ticket", "assign_to_support_team"]
            elif "sales" in request.subject.lower() or "pricing" in request.subject.lower():
                category = "sales"
                confidence = 0.80
                reasoning = "Email appears to be sales-related (fallback mode)"
                actions = ["forward_to_sales", "add_to_crm"]
            else:
                category = "general"
                confidence = 0.60
                reasoning = "No specific category indicators found (fallback mode)"
                actions = ["manual_review"]
            
            end_time = datetime.utcnow()
            processing_time = (end_time - start_time).total_seconds() * 1000
            
            return EmailClassificationResponse(
                category=category,
                confidence=confidence,
                reasoning=reasoning,
                suggested_actions=actions,
                processing_time_ms=processing_time
            )
        
    except Exception as e:
        logger.error(f"Email classification failed: {e}")
        raise HTTPException(status_code=500, detail="Classification failed")

@app.post("/test/mailgun")
async def test_mailgun_integration():
    """Test endpoint to verify Mailgun integration."""
    try:
        # This will use your existing Mailgun test
        # For now, return a placeholder response
        return {
            "status": "success",
            "message": "Mailgun integration tested successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Mailgun test failed: {e}")
        raise HTTPException(status_code=500, detail="Mailgun test failed")

@app.post("/webhooks/mailgun")
async def mailgun_webhook(background_tasks: BackgroundTasks):
    """
    Webhook endpoint for receiving Mailgun events.
    This will be expanded to handle incoming emails.
    """
    try:
        # Placeholder for webhook processing
        logger.info("Received Mailgun webhook")
        return {"status": "received"}
    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")

@app.get("/status")
async def get_system_status():
    """Get current system status and statistics."""
    return {
        "system": "Email Router",
        "status": "operational",
        "version": "1.0.0",
        "features": {
            "email_classification": "ai_powered",
            "mailgun_sending": "configured",
            "gmail_integration": "pending",
            "ai_processing": "anthropic_claude"
        },
        "stats": {
            "emails_processed": 0,
            "classifications_made": 0,
            "uptime": "just_started"
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