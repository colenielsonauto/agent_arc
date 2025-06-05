#!/usr/bin/env python3
"""
AI Email Router - Production FastAPI Application
Handles incoming Mailgun webhooks, classifies emails with Claude 3.5 Sonnet,
generates personalized auto-replies, and forwards to appropriate team members.
"""

import os
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime

from .routers.webhooks import router as webhook_router
from .models.schemas import HealthResponse
from .utils.config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AI Email Router",
    description="AI-powered email classification and routing system",
    version="1.0.0",
    docs_url="/docs"
)

# Add CORS middleware for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(webhook_router, prefix="/webhooks")

@app.get("/", response_model=dict)
async def root():
    """Root endpoint for health check."""
    return {
        "service": "AI Email Router",
        "status": "active",
        "docs": "/docs",
        "health": "/health",
        "webhook": "/webhooks/mailgun/inbound"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for Cloud Run."""
    try:
        config = get_config()
        
        # Test AI service
        ai_status = "configured" if config.anthropic_api_key else "missing_key"
        
        # Test email service  
        email_status = "configured" if config.mailgun_api_key and config.mailgun_domain else "missing_credentials"
        
        return HealthResponse(
            status="healthy",
            timestamp=datetime.utcnow(),
            version="1.0.0",
            components={
                "api": "healthy",
                "ai_classifier": ai_status,
                "email_sender": email_status,
                "webhook_endpoint": "active"
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))  # Cloud Run uses PORT env var
    uvicorn.run("app.main:app", host="0.0.0.0", port=port) 