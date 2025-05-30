"""
Email routing decision entities.

This module defines the core entities for email routing decisions,
including routing rules, destinations, and SLAs.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum

from .classification import EmailCategory, Priority


class RoutingMethod(str, Enum):
    """Methods for routing emails."""
    FORWARD = "forward"
    ASSIGN = "assign"
    QUEUE = "queue"
    ESCALATE = "escalate"
    AUTO_REPLY = "auto_reply"
    ARCHIVE = "archive"


class ResponseTimeUnit(str, Enum):
    """Units for response time SLAs."""
    MINUTES = "minutes"
    HOURS = "hours"
    DAYS = "days"
    WEEKS = "weeks"


@dataclass
class SLA:
    """Service Level Agreement for response times."""
    response_time: int
    unit: ResponseTimeUnit
    business_hours_only: bool = True
    escalation_time: Optional[int] = None
    escalation_unit: Optional[ResponseTimeUnit] = None
    
    def to_timedelta(self) -> timedelta:
        """Convert SLA to timedelta."""
        if self.unit == ResponseTimeUnit.MINUTES:
            return timedelta(minutes=self.response_time)
        elif self.unit == ResponseTimeUnit.HOURS:
            return timedelta(hours=self.response_time)
        elif self.unit == ResponseTimeUnit.DAYS:
            return timedelta(days=self.response_time)
        elif self.unit == ResponseTimeUnit.WEEKS:
            return timedelta(weeks=self.response_time)
        else:
            return timedelta(hours=self.response_time)
    
    def get_deadline(self, from_time: Optional[datetime] = None) -> datetime:
        """Calculate deadline from SLA."""
        start = from_time or datetime.utcnow()
        deadline = start + self.to_timedelta()
        
        # TODO: Implement business hours calculation if needed
        # if self.business_hours_only:
        #     deadline = calculate_business_deadline(start, deadline)
        
        return deadline


@dataclass
class RoutingDestination:
    """A destination for routing emails."""
    name: str
    email: str
    team: Optional[str] = None
    slack_channel: Optional[str] = None
    webhook_url: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __str__(self) -> str:
        if self.team:
            return f"{self.name} ({self.team})"
        return self.name


@dataclass
class RoutingRule:
    """A rule for routing emails."""
    name: str
    category: Optional[EmailCategory] = None
    priority: Optional[Priority] = None
    conditions: Dict[str, Any] = field(default_factory=dict)
    destinations: List[RoutingDestination] = field(default_factory=list)
    method: RoutingMethod = RoutingMethod.FORWARD
    sla: Optional[SLA] = None
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def matches(self, classification: Any, email: Any) -> bool:
        """Check if the rule matches the email and classification."""
        # Check category match
        if self.category and classification.category != self.category:
            return False
        
        # Check priority match
        if self.priority and classification.priority != self.priority:
            return False
        
        # Check custom conditions
        for field, expected in self.conditions.items():
            if field == "confidence_min":
                if classification.confidence < expected:
                    return False
            elif field == "sentiment":
                if classification.sentiment.value != expected:
                    return False
            elif field == "is_urgent":
                if classification.is_urgent != expected:
                    return False
            elif field == "sender_domain":
                if email.sender_domain != expected:
                    return False
            elif field == "has_attachments":
                if email.has_attachments != expected:
                    return False
        
        return True


@dataclass
class RoutingDecision:
    """
    A routing decision for an email.
    
    This represents the complete routing decision including
    destinations, method, SLA, and reasoning.
    """
    email_id: str
    destinations: List[RoutingDestination]
    method: RoutingMethod
    sla: Optional[SLA] = None
    rule_matched: Optional[str] = None
    confidence: float = 1.0
    reasoning: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    decided_at: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def primary_destination(self) -> Optional[RoutingDestination]:
        """Get the primary destination."""
        return self.destinations[0] if self.destinations else None
    
    @property
    def deadline(self) -> Optional[datetime]:
        """Get the response deadline."""
        if self.sla:
            return self.sla.get_deadline(self.decided_at)
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "email_id": self.email_id,
            "destinations": [
                {
                    "name": dest.name,
                    "email": dest.email,
                    "team": dest.team,
                }
                for dest in self.destinations
            ],
            "method": self.method.value,
            "sla": {
                "response_time": self.sla.response_time,
                "unit": self.sla.unit.value,
                "deadline": self.deadline.isoformat() if self.deadline else None,
            } if self.sla else None,
            "rule_matched": self.rule_matched,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "metadata": self.metadata,
            "decided_at": self.decided_at.isoformat(),
        }


@dataclass
class RoutingHistory:
    """History of routing decisions for analysis."""
    email_id: str
    original_decision: RoutingDecision
    redirections: List[RoutingDecision] = field(default_factory=list)
    final_destination: Optional[RoutingDestination] = None
    response_time: Optional[timedelta] = None
    sla_met: Optional[bool] = None
    feedback: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def add_redirection(
        self,
        new_decision: RoutingDecision,
        reason: str
    ) -> None:
        """Add a redirection to the history."""
        new_decision.metadata["redirection_reason"] = reason
        self.redirections.append(new_decision)
        self.final_destination = new_decision.primary_destination
    
    def complete(
        self,
        response_time: timedelta,
        feedback: Optional[str] = None
    ) -> None:
        """Mark the routing as complete."""
        self.response_time = response_time
        
        # Check if SLA was met
        if self.original_decision.sla:
            sla_time = self.original_decision.sla.to_timedelta()
            self.sla_met = response_time <= sla_time
        
        if feedback:
            self.feedback = feedback 