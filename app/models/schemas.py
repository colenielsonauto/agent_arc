"""
Pydantic models for request/response schemas.
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Dict, List, Optional

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: datetime
    version: str
    components: Dict[str, str]

class EmailClassificationRequest(BaseModel):
    """Email classification request."""
    subject: str
    body: str
    sender: Optional[str] = None

class EmailClassificationResponse(BaseModel):
    """Email classification response."""
    category: str
    confidence: float
    reasoning: str
    suggested_actions: List[str]
    processing_time_ms: float

class WebhookResponse(BaseModel):
    """Webhook response."""
    status: str
    message: str 