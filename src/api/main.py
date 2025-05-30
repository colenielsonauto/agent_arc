"""
Main FastAPI application for the Email Router.

This is the entry point for the API, handling both REST endpoints
and webhook integrations.
"""

import logging
from contextlib import asynccontextmanager
from typing import Dict, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ..infrastructure.config import get_settings
from ..core.interfaces.llm_provider import LLMProviderPool, LLMConfig, LLMProvider
from ..core.interfaces.email_provider import EmailProviderConfig, EmailProvider
from ..adapters.llm.gemini import GeminiAdapter
from ..adapters.email.gmail import GmailAdapter

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global state
app_state = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    logger.info("Starting Email Router API...")
    
    # Load configuration
    settings = get_settings()
    app_state["settings"] = settings
    
    # Initialize LLM providers
    try:
        # Create LLM configuration
        llm_config = LLMConfig(
            provider=LLMProvider.GOOGLE,
            model=settings.llm.google_model,
            api_key=settings.llm.google_api_key.get_secret_value() if settings.llm.google_api_key else None,
            temperature=settings.llm.temperature,
            max_tokens=settings.llm.max_tokens,
            timeout=settings.llm.timeout,
        )
        
        gemini_adapter = GeminiAdapter(llm_config)
        llm_pool = LLMProviderPool([gemini_adapter])
        await llm_pool.initialize()
        app_state["llm_pool"] = llm_pool
        logger.info("LLM providers initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize LLM providers: {e}")
        app_state["llm_pool"] = None
    
    # Initialize email providers
    try:
        # Create email configuration
        email_config = EmailProviderConfig(
            provider=EmailProvider.GMAIL,
            credentials={
                "token_path": str(settings.email.gmail_token_path),
                "client_secret_path": str(settings.email.gmail_credentials_path),
                "scopes": settings.email.gmail_scopes,
            },
            polling_interval=settings.email.polling_interval,
            batch_size=settings.email.batch_size,
        )
        
        gmail_adapter = GmailAdapter(email_config)
        app_state["gmail_adapter"] = gmail_adapter
        logger.info("Email providers initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize email providers: {e}")
        app_state["gmail_adapter"] = None
    
    logger.info("Email Router API started successfully")
    
    yield
    
    # Cleanup
    logger.info("Shutting down Email Router API...")
    if app_state.get("gmail_adapter"):
        try:
            await app_state["gmail_adapter"].disconnect()
        except Exception as e:
            logger.error(f"Error disconnecting Gmail adapter: {e}")
    
    logger.info("Email Router API shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Email Router API",
    description="AI-powered email processing and routing system",
    version="2.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoints
@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Basic health check."""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """Detailed health check with component status."""
    settings = app_state.get("settings")
    llm_pool = app_state.get("llm_pool")
    gmail_adapter = app_state.get("gmail_adapter")
    
    # Check LLM health
    llm_healthy = False
    llm_provider_name = None
    if llm_pool and llm_pool.providers:
        try:
            provider = await llm_pool.get_optimal_provider()
            llm_healthy = await provider.health_check()
            llm_provider_name = provider.config.provider.value
        except Exception as e:
            logger.error(f"LLM health check failed: {e}")
    
    # Check Gmail health
    gmail_healthy = False
    if gmail_adapter:
        try:
            gmail_healthy = await gmail_adapter.health_check()
        except Exception as e:
            logger.error(f"Gmail health check failed: {e}")
    
    overall_healthy = llm_healthy and gmail_healthy
    
    return {
        "status": "healthy" if overall_healthy else "unhealthy",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "llm": {
                "status": "healthy" if llm_healthy else "unhealthy",
                "provider": llm_provider_name
            },
            "email": {
                "status": "healthy" if gmail_healthy else "unhealthy",
                "provider": gmail_adapter.config.provider.value if gmail_adapter else None
            },
            "memory": {"status": "not_configured"},
            "analytics": {"status": "not_configured"}
        },
        "configuration": {
            "environment": settings.app.environment if settings else "unknown",
            "debug": settings.app.debug if settings else False
        }
    }


@app.get("/config/validate")
async def validate_configuration() -> Dict[str, Any]:
    """Validate current configuration."""
    settings = app_state.get("settings")
    if not settings:
        raise HTTPException(status_code=500, detail="Settings not loaded")
    
    validation_results = {
        "llm": {
            "provider": settings.llm.default_provider,
            "api_key_configured": bool(settings.llm.google_api_key),
            "model": settings.llm.google_model
        },
        "email": {
            "provider": settings.email.default_provider,
            "credentials_path_exists": settings.email.gmail_credentials_path.exists(),
            "token_path_exists": settings.email.gmail_token_path.exists()
        },
        "security": {
            "jwt_secret_configured": bool(settings.security.jwt_secret),
            "encryption_enabled": settings.security.use_encryption
        }
    }
    
    return {
        "status": "configuration_loaded",
        "timestamp": datetime.utcnow().isoformat(),
        "validation": validation_results
    }


# Test endpoints for development
@app.post("/test/classify")
async def test_classification(text: str) -> Dict[str, Any]:
    """Test email classification endpoint."""
    llm_pool = app_state.get("llm_pool")
    if not llm_pool:
        raise HTTPException(status_code=503, detail="LLM providers not available")
    
    try:
        provider = await llm_pool.get_optimal_provider()
        result = await provider.classify(
            text=text,
            categories=["support", "sales", "billing", "technical", "other"]
        )
        
        return {
            "status": "success",
            "result": {
                "category": result.category,
                "confidence": result.confidence,
                "reasoning": result.reasoning
            },
            "metadata": result.metadata
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")


# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if app_state.get("settings", {}).app.debug else "An error occurred",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 