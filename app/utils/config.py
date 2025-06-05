"""
Clean configuration management with environment variables.
🔧 Optimized for Cloud Run deployment.
"""

import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class Config:
    """Application configuration loaded from environment variables."""
    
    # Anthropic Claude (Required)
    anthropic_api_key: str
    anthropic_model: str
    
    # Mailgun (Required)
    mailgun_api_key: str
    mailgun_domain: str
    
    # Google Cloud (Optional for production)
    google_project_id: Optional[str] = None
    google_region: Optional[str] = None
    
    # Application settings
    environment: str = "production"
    port: int = 8080
    log_level: str = "INFO"

def get_config() -> Config:
    """
    Load configuration from environment variables.
    
    Required environment variables:
    - ANTHROPIC_API_KEY: Your Anthropic API key
    - MAILGUN_API_KEY: Your Mailgun API key  
    - MAILGUN_DOMAIN: Your Mailgun domain
    
    Optional environment variables:
    - ANTHROPIC_MODEL: Claude model (default: claude-3-5-sonnet-20241022)
    - GOOGLE_CLOUD_PROJECT: Google Cloud project ID
    - GOOGLE_CLOUD_REGION: Google Cloud region (default: us-central1)
    - ENVIRONMENT: Application environment (default: production)
    - PORT: Server port (default: 8080)
    - LOG_LEVEL: Logging level (default: INFO)
    """
    
    # Validate required environment variables
    required_vars = ["ANTHROPIC_API_KEY", "MAILGUN_API_KEY", "MAILGUN_DOMAIN"]
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    return Config(
        # Required
        anthropic_api_key=os.environ["ANTHROPIC_API_KEY"],
        mailgun_api_key=os.environ["MAILGUN_API_KEY"],
        mailgun_domain=os.environ["MAILGUN_DOMAIN"],
        
        # Optional with defaults
        anthropic_model=os.environ.get("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"),
        google_project_id=os.environ.get("GOOGLE_CLOUD_PROJECT"),
        google_region=os.environ.get("GOOGLE_CLOUD_REGION", "us-central1"),
        environment=os.environ.get("ENVIRONMENT", "production"),
        port=int(os.environ.get("PORT", 8080)),
        log_level=os.environ.get("LOG_LEVEL", "INFO")
    ) 