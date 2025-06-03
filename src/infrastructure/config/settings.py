"""
Centralized configuration management using Pydantic.

This module provides type-safe configuration management with
validation, environment variable support, and secret handling.
"""

from typing import Dict, List, Optional, Any
from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings
from pathlib import Path
import os


class LLMSettings(BaseSettings):
    """LLM provider settings."""
    
    # Default provider - Changed to Anthropic for privacy
    default_provider: str = Field("anthropic", env="LLM_DEFAULT_PROVIDER")
    
    # Google Gemini
    google_api_key: Optional[SecretStr] = Field(None, env="GOOGLE_API_KEY")
    google_model: str = Field("gemini-1.5-pro", env="GOOGLE_MODEL")
    
    # OpenAI
    openai_api_key: Optional[SecretStr] = Field(None, env="OPENAI_API_KEY")
    openai_model: str = Field("gpt-4-turbo-preview", env="OPENAI_MODEL")
    openai_org_id: Optional[str] = Field(None, env="OPENAI_ORG_ID")
    
    # Anthropic
    anthropic_api_key: Optional[SecretStr] = Field(
        SecretStr("your-anthropic-api-key-here"),
        env="ANTHROPIC_API_KEY"
    )
    anthropic_model: str = Field("claude-3-5-sonnet-20241022", env="ANTHROPIC_MODEL")
    
    # Common settings
    temperature: float = Field(0.7, ge=0.0, le=2.0, env="LLM_TEMPERATURE")
    max_tokens: Optional[int] = Field(2000, env="LLM_MAX_TOKENS")
    timeout: int = Field(30, env="LLM_TIMEOUT")
    
    model_config = {"extra": "allow", "case_sensitive": False}


class EmailSettings(BaseSettings):
    """Email provider settings."""
    
    # Default provider
    default_provider: str = Field("gmail", env="EMAIL_DEFAULT_PROVIDER")
    
    # Gmail
    gmail_credentials_path: Path = Field(
        ".secrets/oauth_client.json",
        env="GMAIL_CREDENTIALS_PATH"
    )
    gmail_token_path: Path = Field(
        ".secrets/token.json",
        env="GMAIL_TOKEN_PATH"
    )
    gmail_scopes: List[str] = Field(
        default_factory=lambda: [
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/gmail.send",
            "https://www.googleapis.com/auth/gmail.compose",
            "https://www.googleapis.com/auth/gmail.modify"
        ]
    )
    
    # Mailgun
    mailgun_api_key: Optional[SecretStr] = Field(
        None,
        env="MAILGUN_API_KEY"
    )
    mailgun_domain: Optional[str] = Field(
        "mail.colesportfolio.com",
        env="MAILGUN_DOMAIN"
    )
    mailgun_base_url: str = Field(
        "https://api.mailgun.net",
        env="MAILGUN_BASE_URL"
    )
    
    # Common settings
    polling_interval: int = Field(60, env="EMAIL_POLLING_INTERVAL")
    batch_size: int = Field(50, env="EMAIL_BATCH_SIZE")
    
    @field_validator("gmail_credentials_path", "gmail_token_path")
    @classmethod
    def validate_path(cls, v):
        """Ensure paths exist or can be created."""
        path = Path(v)
        if not path.exists() and not path.parent.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
        return path


class MemorySettings(BaseSettings):
    """Memory store settings."""
    
    # Default store
    default_store: str = Field("redis", env="MEMORY_DEFAULT_STORE")
    
    # Redis
    redis_url: str = Field("redis://localhost:6379", env="REDIS_URL")
    redis_password: Optional[SecretStr] = Field(None, env="REDIS_PASSWORD")
    redis_db: int = Field(0, env="REDIS_DB")
    
    # Pinecone
    pinecone_api_key: Optional[SecretStr] = Field(None, env="PINECONE_API_KEY")
    pinecone_environment: Optional[str] = Field(None, env="PINECONE_ENVIRONMENT")
    pinecone_index: Optional[str] = Field(None, env="PINECONE_INDEX")
    
    # PostgreSQL
    postgres_url: Optional[str] = Field(None, env="DATABASE_URL")
    
    # Common settings
    embedding_dimension: int = Field(1536, env="EMBEDDING_DIMENSION")
    default_ttl: Optional[int] = Field(86400, env="MEMORY_DEFAULT_TTL")  # 24 hours
    
    model_config = {"extra": "allow", "case_sensitive": False}


class AnalyticsSettings(BaseSettings):
    """Analytics and monitoring settings."""
    
    # Default sink
    default_sink: str = Field("prometheus", env="ANALYTICS_DEFAULT_SINK")
    
    # Prometheus
    prometheus_pushgateway: Optional[str] = Field(
        None,
        env="PROMETHEUS_PUSHGATEWAY"
    )
    
    # Datadog
    datadog_api_key: Optional[SecretStr] = Field(None, env="DATADOG_API_KEY")
    datadog_app_key: Optional[SecretStr] = Field(None, env="DATADOG_APP_KEY")
    
    # LangSmith
    langsmith_api_key: Optional[SecretStr] = Field(None, env="LANGSMITH_API_KEY")
    langsmith_project: Optional[str] = Field(None, env="LANGSMITH_PROJECT")
    
    # Common settings
    enable_tracing: bool = Field(True, env="ENABLE_TRACING")
    enable_metrics: bool = Field(True, env="ENABLE_METRICS")
    sampling_rate: float = Field(1.0, ge=0.0, le=1.0, env="SAMPLING_RATE")
    
    model_config = {"extra": "allow", "case_sensitive": False}


class SecuritySettings(BaseSettings):
    """Security settings."""
    
    # Encryption
    encryption_key: Optional[SecretStr] = Field(None, env="ENCRYPTION_KEY")
    use_encryption: bool = Field(True, env="USE_ENCRYPTION")
    
    # Key management
    vault_url: Optional[str] = Field(None, env="VAULT_URL")
    vault_token: Optional[SecretStr] = Field(None, env="VAULT_TOKEN")
    
    # JWT
    jwt_secret: SecretStr = Field(..., env="JWT_SECRET")
    jwt_algorithm: str = Field("HS256", env="JWT_ALGORITHM")
    jwt_expiry_minutes: int = Field(15, env="JWT_EXPIRY_MINUTES")
    
    # API Keys
    api_key_header: str = Field("X-API-Key", env="API_KEY_HEADER")
    
    model_config = {"extra": "allow", "case_sensitive": False}


class ApplicationSettings(BaseSettings):
    """Main application settings."""
    
    # Environment
    environment: str = Field("development", env="ENVIRONMENT")
    debug: bool = Field(False, env="DEBUG")
    
    # Logging
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_format: str = Field("json", env="LOG_FORMAT")  # json or text
    
    # API
    api_host: str = Field("0.0.0.0", env="API_HOST")
    api_port: int = Field(8000, env="API_PORT")
    api_prefix: str = Field("/api/v1", env="API_PREFIX")
    
    # Cloud Function
    cloud_function_name: str = Field("email-router", env="FUNCTION_NAME")
    cloud_function_region: str = Field("us-central1", env="FUNCTION_REGION")
    
    # Pub/Sub
    pubsub_topic: str = Field("email-inbound", env="PUBSUB_TOPIC")
    pubsub_subscription: str = Field("email-inbound-sub", env="PUBSUB_SUBSCRIPTION")
    
    # Processing
    max_retries: int = Field(3, env="MAX_RETRIES")
    retry_delay: int = Field(5, env="RETRY_DELAY")  # seconds
    
    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v):
        """Validate environment name."""
        valid = ["development", "staging", "production"]
        if v not in valid:
            raise ValueError(f"Environment must be one of: {valid}")
        return v
    
    model_config = {
        "extra": "allow", 
        "case_sensitive": False,
        "env_file": ".env",
        "env_file_encoding": "utf-8"
    }


class Settings(BaseSettings):
    """Combined settings for the entire application."""
    
    # Sub-settings
    llm: LLMSettings = Field(default_factory=LLMSettings)
    email: EmailSettings = Field(default_factory=EmailSettings)
    memory: MemorySettings = Field(default_factory=MemorySettings)
    analytics: AnalyticsSettings = Field(default_factory=AnalyticsSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    app: ApplicationSettings = Field(default_factory=ApplicationSettings)
    
    # Feature flags
    enable_memory: bool = Field(True, env="ENABLE_MEMORY")
    enable_analytics: bool = Field(True, env="ENABLE_ANALYTICS")
    enable_multi_agent: bool = Field(False, env="ENABLE_MULTI_AGENT")
    enable_webhooks: bool = Field(True, env="ENABLE_WEBHOOKS")
    
    model_config = {
        "extra": "allow", 
        "case_sensitive": False,
        "env_file": ".env",
        "env_file_encoding": "utf-8"
    }
    
    @classmethod
    def load(cls) -> "Settings":
        """Load settings with environment variable support."""
        # Load from .env file if it exists
        env_file = Path(".env")
        if env_file.exists():
            from dotenv import load_dotenv
            load_dotenv(env_file)
        
        return cls()
    
    def get_llm_config(self, provider: Optional[str] = None) -> Dict[str, Any]:
        """Get LLM configuration for a specific provider."""
        provider = provider or self.llm.default_provider
        
        if provider == "google":
            return {
                "provider": "google",
                "api_key": self.llm.google_api_key.get_secret_value() if self.llm.google_api_key else None,
                "model": self.llm.google_model,
                "temperature": self.llm.temperature,
                "max_tokens": self.llm.max_tokens,
                "timeout": self.llm.timeout,
            }
        elif provider == "openai":
            return {
                "provider": "openai",
                "api_key": self.llm.openai_api_key.get_secret_value() if self.llm.openai_api_key else None,
                "model": self.llm.openai_model,
                "organization": self.llm.openai_org_id,
                "temperature": self.llm.temperature,
                "max_tokens": self.llm.max_tokens,
                "timeout": self.llm.timeout,
            }
        elif provider == "anthropic":
            return {
                "provider": "anthropic",
                "api_key": self.llm.anthropic_api_key.get_secret_value() if self.llm.anthropic_api_key else None,
                "model": self.llm.anthropic_model,
                "temperature": self.llm.temperature,
                "max_tokens": self.llm.max_tokens,
                "timeout": self.llm.timeout,
            }
        else:
            raise ValueError(f"Unknown LLM provider: {provider}")
    
    def get_email_config(self, provider: Optional[str] = None) -> Dict[str, Any]:
        """Get email configuration for a specific provider."""
        provider = provider or self.email.default_provider
        
        if provider == "gmail":
            return {
                "provider": "gmail",
                "credentials": {
                    "token_path": str(self.email.gmail_token_path),
                    "client_secret_path": str(self.email.gmail_credentials_path),
                    "scopes": self.email.gmail_scopes,
                },
                "polling_interval": self.email.polling_interval,
                "batch_size": self.email.batch_size,
            }
        elif provider == "mailgun":
            return {
                "provider": "mailgun",
                "credentials": {
                    "api_key": self.email.mailgun_api_key.get_secret_value() if self.email.mailgun_api_key else None,
                    "domain": self.email.mailgun_domain,
                    "base_url": self.email.mailgun_base_url,
                },
                "polling_interval": self.email.polling_interval,
                "batch_size": self.email.batch_size,
            }
        else:
            raise ValueError(f"Unknown email provider: {provider}")


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings.load()
    return _settings

def reload_settings() -> Settings:
    """Force reload settings from environment."""
    global _settings
    _settings = Settings.load()
    return _settings 