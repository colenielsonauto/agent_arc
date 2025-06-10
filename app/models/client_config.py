"""
Pydantic models for client configuration validation.
🏗️ Defines schemas for YAML configuration files.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field, EmailStr, validator, field_validator


class ClientStatus(str, Enum):
    """Client status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive" 
    TRIAL = "trial"
    SUSPENDED = "suspended"


class Priority(str, Enum):
    """Priority level enumeration."""
    URGENT = "urgent"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ClientInfo(BaseModel):
    """Core client information."""
    id: str
    name: str
    industry: str
    status: str = "active"
    timezone: str = "UTC"
    business_hours: str = "9-17"  # "start-end" format
    
    @field_validator('id')
    @classmethod
    def validate_client_id(cls, v: str) -> str:
        """Validate client ID format."""
        if not v.startswith('client-'):
            raise ValueError('Client ID must start with "client-"')
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Client ID must contain only alphanumeric characters, hyphens, and underscores')
        return v


class DomainConfig(BaseModel):
    """Email domain configuration."""
    primary: str = Field(..., description="Primary company domain")
    support: EmailStr = Field(..., description="Support email address")
    mailgun: str = Field(..., description="Mailgun domain for sending")


class BrandingConfig(BaseModel):
    """Client branding configuration."""
    company_name: str
    email_signature: str
    primary_color: str = "#667eea"
    secondary_color: str = "#764ba2"
    
    @field_validator('primary_color', 'secondary_color')
    @classmethod  
    def validate_hex_color(cls, v: str) -> str:
        """Validate hex color format."""
        if not v.startswith('#') or len(v) != 7:
            raise ValueError('Color must be a valid hex color (e.g., #667eea)')
        try:
            int(v[1:], 16)  # Try to parse as hex
        except ValueError:
            raise ValueError('Color must be a valid hex color (e.g., #667eea)')
        return v


class ResponseTimeConfig(BaseModel):
    """Response time commitments."""
    support: str = Field(..., description="Support response time")
    billing: str = Field(..., description="Billing response time")
    sales: str = Field(..., description="Sales response time")  
    general: str = Field(..., description="General response time")


class ContactsConfig(BaseModel):
    """Contact information."""
    primary_contact: EmailStr = Field(..., description="Primary contact email")
    escalation_contact: EmailStr = Field(..., description="Escalation contact email")
    billing_contact: EmailStr = Field(..., description="Billing contact email")


class SettingsConfig(BaseModel):
    """Feature flags and settings."""
    auto_reply_enabled: bool = Field(default=True, description="Enable automatic replies")
    team_forwarding_enabled: bool = Field(default=True, description="Forward to team members")
    ai_classification_enabled: bool = Field(default=True, description="Use AI for classification")
    escalation_enabled: bool = Field(default=True, description="Auto-escalate based on rules")
    monitoring_enabled: bool = Field(default=True, description="Enable monitoring/analytics")


class ClientConfig(BaseModel):
    """Complete client configuration."""
    client: ClientInfo
    domains: DomainConfig
    branding: BrandingConfig
    response_times: ResponseTimeConfig
    contacts: ContactsConfig
    settings: SettingsConfig = Field(default_factory=SettingsConfig)
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Routing Models

class EscalationRule(BaseModel):
    """Single escalation rule."""
    hours: int = Field(..., description="Hours after which to escalate")
    escalate_to: EmailStr = Field(..., description="Email address to escalate to")


class TimeBasedEscalation(BaseModel):
    """Time-based escalation configuration."""
    support: Optional[List[EscalationRule]] = None
    billing: Optional[List[EscalationRule]] = None
    sales: Optional[List[EscalationRule]] = None
    general: Optional[List[EscalationRule]] = None


class EscalationConfig(BaseModel):
    """Escalation configuration."""
    time_based: Optional[TimeBasedEscalation] = None
    keyword_based: Optional[Dict[str, EmailStr]] = None


class SpecialRules(BaseModel):
    """Special routing rules."""
    vip_domains: List[str] = Field(default_factory=list)
    vip_route_to: Optional[EmailStr] = None
    after_hours_route_to: Optional[EmailStr] = None
    weekend_route_to: Optional[EmailStr] = None


class RoutingRules(BaseModel):
    """Email routing rules configuration."""
    routing: Dict[str, EmailStr] = Field(..., description="Category to email mapping")
    escalation: Optional[EscalationConfig] = None
    backup_routing: Optional[Dict[str, EmailStr]] = None
    special_rules: Optional[SpecialRules] = None


# Category Models

class CategoryConfig(BaseModel):
    """Email category configuration."""
    name: str = Field(..., description="Category display name")
    description: str = Field(..., description="Category description")
    priority: Priority = Field(..., description="Default priority level")
    keywords: List[str] = Field(default_factory=list, description="Keywords for classification")
    confidence_threshold: float = Field(0.8, description="Minimum confidence threshold")
    
    @field_validator('confidence_threshold')
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        """Validate confidence threshold is between 0 and 1."""
        if not 0 <= v <= 1:
            raise ValueError('Confidence threshold must be between 0 and 1')
        return v


class PriorityLevel(BaseModel):
    """Priority level configuration."""
    response_time: str = Field(..., description="Expected response time")
    escalate_immediately: bool = Field(default=False, description="Escalate immediately")
    escalate_after: Optional[int] = Field(None, description="Hours after which to escalate")


class FallbackConfig(BaseModel):
    """Fallback configuration."""
    default_category: str = Field(default="general", description="Default category")
    minimum_confidence: float = Field(0.5, description="Minimum confidence for classification")
    unknown_threshold: float = Field(0.3, description="Threshold for unknown classification")


class CategoriesConfig(BaseModel):
    """Categories configuration."""
    categories: Dict[str, CategoryConfig] = Field(..., description="Primary categories")
    specialized_categories: Optional[Dict[str, CategoryConfig]] = None
    priority_levels: Dict[Priority, PriorityLevel] = Field(..., description="Priority level definitions")
    fallback: FallbackConfig = Field(default_factory=FallbackConfig)


# SLA Models

class ResponseTimeTarget(BaseModel):
    """Response time target configuration."""
    target: str = Field(..., description="Target response time")
    business_hours_only: bool = Field(default=True, description="Only during business hours")
    weekend_multiplier: float = Field(1.0, description="Weekend response time multiplier")


class BusinessHours(BaseModel):
    """Business hours configuration."""
    timezone: str = Field(..., description="Business timezone")
    workdays: List[str] = Field(..., description="Work days of the week")
    start_time: str = Field(..., description="Start time (HH:MM)")
    end_time: str = Field(..., description="End time (HH:MM)")
    holidays: List[str] = Field(default_factory=list, description="Holiday dates (YYYY-MM-DD)")


class SLAConfig(BaseModel):
    """Service Level Agreement configuration."""
    response_times: Dict[str, ResponseTimeTarget] = Field(..., description="Response time targets")
    business_hours: BusinessHours = Field(..., description="Business hours definition")
    # Additional SLA fields can be added here as needed 


class AISettings(BaseModel):
    """AI processing settings for client."""
    ai_classification_enabled: bool = True
    ai_response_enabled: bool = True
    confidence_threshold: float = 0.5
    ai_model_preferences: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('confidence_threshold')
    @classmethod
    def validate_confidence_threshold(cls, v: float) -> float:
        """Validate confidence threshold is between 0 and 1."""
        if not 0 <= v <= 1:
            raise ValueError('Confidence threshold must be between 0 and 1')
        return v 