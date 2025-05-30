"""
Core domain logic for the email router system.

This package contains the business logic, entities, and interfaces
that define the core functionality of the system.
"""

# Version
__version__ = "2.0.0"

# Import key components for easier access
from .entities.email import Email, EmailAddress, EmailAttachment
from .entities.classification import Classification, EmailCategory, Priority
from .entities.routing_decision import RoutingDecision, RoutingDestination, SLA

from .interfaces.llm_provider import (
    LLMProviderInterface,
    LLMProviderPool,
    LLMConfig,
    LLMProvider,
)
from .interfaces.email_provider import (
    EmailProviderInterface,
    EmailProviderConfig,
    EmailProvider,
    EmailFilter,
)
from .interfaces.memory_store import (
    MemoryStoreInterface,
    MemoryStoreConfig,
    MemoryEntry,
    ConversationContext,
)
from .interfaces.analytics_sink import (
    AnalyticsSinkInterface,
    AnalyticsConfig,
    EmailProcessingMetrics,
)

__all__ = [
    # Entities
    "Email",
    "EmailAddress",
    "EmailAttachment",
    "Classification",
    "EmailCategory",
    "Priority",
    "RoutingDecision",
    "RoutingDestination",
    "SLA",
    # Interfaces
    "LLMProviderInterface",
    "LLMProviderPool",
    "LLMConfig",
    "LLMProvider",
    "EmailProviderInterface",
    "EmailProviderConfig",
    "EmailProvider",
    "EmailFilter",
    "MemoryStoreInterface",
    "MemoryStoreConfig",
    "MemoryEntry",
    "ConversationContext",
    "AnalyticsSinkInterface",
    "AnalyticsConfig",
    "EmailProcessingMetrics",
] 