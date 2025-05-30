"""
Email classification entities.

This module defines the core entities for email classification,
including categories, confidence scores, and routing decisions.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class EmailCategory(str, Enum):
    """Standard email categories."""
    SUPPORT = "support"
    SALES = "sales"
    BILLING = "billing"
    TECHNICAL = "technical"
    FEEDBACK = "feedback"
    COMPLAINT = "complaint"
    INQUIRY = "inquiry"
    SPAM = "spam"
    OTHER = "other"
    
    @classmethod
    def from_string(cls, value: str) -> "EmailCategory":
        """Convert string to EmailCategory, with fallback to OTHER."""
        try:
            return cls(value.lower())
        except ValueError:
            # Try to match by name
            for category in cls:
                if category.name.lower() == value.lower():
                    return category
            return cls.OTHER


class Priority(str, Enum):
    """Email priority levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Sentiment(str, Enum):
    """Email sentiment."""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    ANGRY = "angry"


@dataclass
class Classification:
    """
    Email classification result.
    
    This represents the full classification of an email, including
    category, confidence, priority, and extracted metadata.
    """
    category: EmailCategory
    confidence: float
    sub_categories: List[str] = field(default_factory=list)
    priority: Priority = Priority.MEDIUM
    sentiment: Sentiment = Sentiment.NEUTRAL
    intent: Optional[str] = None
    entities: Dict[str, List[str]] = field(default_factory=dict)
    keywords: List[str] = field(default_factory=list)
    language: str = "en"
    is_urgent: bool = False
    requires_human_review: bool = False
    reasoning: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    classified_at: datetime = field(default_factory=datetime.utcnow)
    classifier_version: str = "1.0.0"
    
    def __post_init__(self):
        """Validate and process classification data."""
        # Ensure confidence is between 0 and 1
        self.confidence = max(0.0, min(1.0, self.confidence))
        
        # Auto-detect urgency based on keywords or priority
        if self.priority in [Priority.CRITICAL, Priority.HIGH]:
            self.is_urgent = True
        
        # Flag for human review if confidence is too low
        if self.confidence < 0.7:
            self.requires_human_review = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "category": self.category.value,
            "confidence": self.confidence,
            "sub_categories": self.sub_categories,
            "priority": self.priority.value,
            "sentiment": self.sentiment.value,
            "intent": self.intent,
            "entities": self.entities,
            "keywords": self.keywords,
            "language": self.language,
            "is_urgent": self.is_urgent,
            "requires_human_review": self.requires_human_review,
            "reasoning": self.reasoning,
            "metadata": self.metadata,
            "classified_at": self.classified_at.isoformat(),
            "classifier_version": self.classifier_version,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Classification":
        """Create from dictionary."""
        # Convert string values to enums
        data["category"] = EmailCategory.from_string(data["category"])
        data["priority"] = Priority(data.get("priority", "medium"))
        data["sentiment"] = Sentiment(data.get("sentiment", "neutral"))
        
        # Convert ISO string to datetime
        if "classified_at" in data and isinstance(data["classified_at"], str):
            data["classified_at"] = datetime.fromisoformat(data["classified_at"])
        
        return cls(**data)


@dataclass
class ClassificationRule:
    """
    A rule for email classification.
    
    Rules can be used to override AI classification for specific patterns
    or to provide additional classification hints.
    """
    name: str
    category: EmailCategory
    priority: Priority = Priority.MEDIUM
    conditions: Dict[str, Any] = field(default_factory=dict)
    actions: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def matches(self, email_content: Dict[str, Any]) -> bool:
        """Check if the rule matches the email content."""
        # Simple pattern matching for now
        # Can be extended with more complex logic
        for field, pattern in self.conditions.items():
            if field not in email_content:
                return False
            
            if isinstance(pattern, str):
                if pattern.lower() not in str(email_content[field]).lower():
                    return False
            elif isinstance(pattern, list):
                if not any(p.lower() in str(email_content[field]).lower() for p in pattern):
                    return False
        
        return True


@dataclass
class ClassificationHistory:
    """
    History of classifications for analysis and improvement.
    """
    email_id: str
    original_classification: Classification
    corrections: List[Classification] = field(default_factory=list)
    feedback: Optional[str] = None
    corrected_by: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def add_correction(
        self,
        corrected_classification: Classification,
        corrected_by: str,
        feedback: Optional[str] = None
    ) -> None:
        """Add a correction to the history."""
        self.corrections.append(corrected_classification)
        self.corrected_by = corrected_by
        if feedback:
            self.feedback = feedback
    
    @property
    def final_classification(self) -> Classification:
        """Get the final (most recent) classification."""
        if self.corrections:
            return self.corrections[-1]
        return self.original_classification 