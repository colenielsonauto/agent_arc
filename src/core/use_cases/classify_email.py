"""
Email classification use case.

This module implements the business logic for classifying emails,
using the abstract LLM interface to ensure provider independence.
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from ..entities.email import Email
from ..entities.classification import (
    Classification,
    EmailCategory,
    Priority,
    Sentiment,
    ClassificationRule,
)
from ..interfaces.llm_provider import (
    LLMProviderInterface,
    LLMProviderPool,
)
from ..interfaces.memory_store import (
    MemoryStoreInterface,
    MemoryEntry,
    SearchQuery,
)
from ..interfaces.analytics_sink import (
    AnalyticsSinkInterface,
    EmailProcessingMetrics,
)

logger = logging.getLogger(__name__)


class EmailClassifier:
    """
    Use case for classifying emails.
    
    This class orchestrates the email classification process,
    including rule-based classification, AI classification,
    context retrieval, and analytics tracking.
    """
    
    def __init__(
        self,
        llm_pool: LLMProviderPool,
        memory_store: Optional[MemoryStoreInterface] = None,
        analytics: Optional[AnalyticsSinkInterface] = None,
        rules: Optional[List[ClassificationRule]] = None,
    ):
        """
        Initialize the email classifier.
        
        Args:
            llm_pool: Pool of LLM providers for classification
            memory_store: Optional memory store for context
            analytics: Optional analytics sink for tracking
            rules: Optional list of classification rules
        """
        self.llm_pool = llm_pool
        self.memory_store = memory_store
        self.analytics = analytics
        self.rules = rules or []
        self._categories = [cat.value for cat in EmailCategory]
    
    async def classify(
        self,
        email: Email,
        user_id: Optional[str] = None,
        use_context: bool = True,
    ) -> Classification:
        """
        Classify an email.
        
        Args:
            email: The email to classify
            user_id: Optional user ID for personalized classification
            use_context: Whether to use historical context
            
        Returns:
            Classification result
        """
        start_time = datetime.utcnow()
        
        # Check rule-based classification first
        rule_classification = self._apply_rules(email)
        if rule_classification and rule_classification.confidence >= 0.95:
            # High confidence rule match, use it
            await self._track_classification(
                email, rule_classification, user_id, start_time, "rule"
            )
            return rule_classification
        
        # Gather context if available
        context = {}
        if use_context and self.memory_store and user_id:
            context = await self._gather_context(email, user_id)
        
        # Prepare classification text
        classification_text = self._prepare_classification_text(email)
        
        # Get LLM classification
        try:
            llm_provider = await self.llm_pool.get_optimal_provider()
            
            # Add examples if we have context
            examples = []
            if context.get("similar_emails"):
                examples = [
                    {
                        "text": similar["subject"],
                        "category": similar["category"]
                    }
                    for similar in context["similar_emails"][:3]
                ]
            
            # Perform classification
            result = await llm_provider.classify(
                text=classification_text,
                categories=self._categories,
                examples=examples,
                context=context
            )
            
            # Extract detailed information
            details_schema = {
                "type": "object",
                "properties": {
                    "priority": {"type": "string", "enum": ["critical", "high", "medium", "low"]},
                    "sentiment": {"type": "string", "enum": ["positive", "neutral", "negative", "angry"]},
                    "intent": {"type": "string"},
                    "entities": {
                        "type": "object",
                        "properties": {
                            "people": {"type": "array", "items": {"type": "string"}},
                            "organizations": {"type": "array", "items": {"type": "string"}},
                            "dates": {"type": "array", "items": {"type": "string"}},
                            "amounts": {"type": "array", "items": {"type": "string"}},
                        }
                    },
                    "keywords": {"type": "array", "items": {"type": "string"}},
                    "is_urgent": {"type": "boolean"},
                }
            }
            
            extracted = await llm_provider.extract_structured(
                text=email.body_text,
                schema=details_schema
            )
            
            # Build classification
            classification = Classification(
                category=EmailCategory.from_string(result.category),
                confidence=result.confidence,
                priority=Priority(extracted.get("priority", "medium")),
                sentiment=Sentiment(extracted.get("sentiment", "neutral")),
                intent=extracted.get("intent"),
                entities=extracted.get("entities", {}),
                keywords=extracted.get("keywords", []),
                is_urgent=extracted.get("is_urgent", False),
                reasoning=result.reasoning,
                metadata={
                    "llm_provider": llm_provider.config.provider.value,
                    "llm_model": llm_provider.config.model,
                    "processing_time_ms": result.metadata.get("duration_ms", 0),
                }
            )
            
            # Merge with rule classification if available
            if rule_classification:
                classification = self._merge_classifications(
                    rule_classification, classification
                )
            
            # Store in memory for future context
            if self.memory_store and user_id:
                await self._store_classification(email, classification, user_id)
            
            # Track analytics
            await self._track_classification(
                email, classification, user_id, start_time, "ai"
            )
            
            return classification
            
        except Exception as e:
            logger.error(f"Error during classification: {e}")
            
            # Fallback classification
            fallback = Classification(
                category=EmailCategory.OTHER,
                confidence=0.0,
                requires_human_review=True,
                reasoning=f"Classification failed: {str(e)}"
            )
            
            await self._track_classification(
                email, fallback, user_id, start_time, "error"
            )
            
            return fallback
    
    def _apply_rules(self, email: Email) -> Optional[Classification]:
        """Apply classification rules to the email."""
        email_content = {
            "from": email.from_address.email,
            "subject": email.subject,
            "body": email.body_text,
            "domain": email.sender_domain,
            "has_attachments": email.has_attachments,
        }
        
        for rule in self.rules:
            if rule.enabled and rule.matches(email_content):
                return Classification(
                    category=rule.category,
                    confidence=1.0,
                    priority=rule.priority,
                    reasoning=f"Matched rule: {rule.name}",
                    metadata={"rule_name": rule.name}
                )
        
        return None
    
    async def _gather_context(
        self,
        email: Email,
        user_id: str
    ) -> Dict[str, Any]:
        """Gather context from memory store."""
        context = {}
        
        try:
            # Get user preferences
            preferences = await self.memory_store.get_user_preferences(user_id)
            if preferences:
                context["user_preferences"] = preferences.preferences
                context["routing_rules"] = preferences.routing_rules
            
            # Search for similar emails
            search_query = SearchQuery(
                query=f"{email.subject} {email.body_text[:200]}",
                user_id=user_id,
                limit=5,
                filters={"type": "email_classification"}
            )
            
            similar_results = await self.memory_store.search_memories(search_query)
            if similar_results:
                context["similar_emails"] = [
                    entry.metadata for entry, score in similar_results
                    if score > 0.7
                ]
            
            # Get conversation context if thread exists
            if email.thread_id:
                conv_context = await self.memory_store.get_conversation_context(
                    email.thread_id, user_id
                )
                if conv_context:
                    context["conversation_history"] = [
                        msg.content for msg in conv_context.get_context_window(5)
                    ]
        
        except Exception as e:
            logger.error(f"Error gathering context: {e}")
        
        return context
    
    def _prepare_classification_text(self, email: Email) -> str:
        """Prepare text for classification."""
        # Combine relevant fields for classification
        parts = [
            f"From: {email.from_address.email}",
            f"Subject: {email.subject}",
            f"Body: {email.body_text[:1000]}",  # Limit body length
        ]
        
        if email.has_attachments:
            parts.append(f"Attachments: {len(email.attachments)} files")
        
        return "\n".join(parts)
    
    def _merge_classifications(
        self,
        rule_classification: Classification,
        ai_classification: Classification
    ) -> Classification:
        """Merge rule-based and AI classifications."""
        # If rule has high confidence, use its category
        if rule_classification.confidence >= 0.95:
            ai_classification.category = rule_classification.category
            ai_classification.metadata["rule_override"] = True
        
        # Keep the more specific priority
        if rule_classification.priority != Priority.MEDIUM:
            ai_classification.priority = rule_classification.priority
        
        # Merge metadata
        ai_classification.metadata.update(rule_classification.metadata)
        
        return ai_classification
    
    async def _store_classification(
        self,
        email: Email,
        classification: Classification,
        user_id: str
    ) -> None:
        """Store classification in memory for future context."""
        if not self.memory_store:
            return
        
        try:
            memory_entry = MemoryEntry(
                user_id=user_id,
                content=f"{email.subject}\n{email.body_text[:500]}",
                metadata={
                    "type": "email_classification",
                    "email_id": email.id,
                    "thread_id": email.thread_id,
                    "from": email.from_address.email,
                    "subject": email.subject,
                    "category": classification.category.value,
                    "confidence": classification.confidence,
                    "priority": classification.priority.value,
                    "sentiment": classification.sentiment.value,
                    "timestamp": classification.classified_at.isoformat(),
                }
            )
            
            await self.memory_store.store_memory(memory_entry)
            
        except Exception as e:
            logger.error(f"Error storing classification: {e}")
    
    async def _track_classification(
        self,
        email: Email,
        classification: Classification,
        user_id: Optional[str],
        start_time: datetime,
        method: str
    ) -> None:
        """Track classification metrics."""
        if not self.analytics:
            return
        
        try:
            processing_time_ms = (
                datetime.utcnow() - start_time
            ).total_seconds() * 1000
            
            metrics = EmailProcessingMetrics(
                email_id=email.id,
                user_id=user_id or "anonymous",
                classification=classification.category.value,
                confidence=classification.confidence,
                processing_time_ms=processing_time_ms,
                llm_provider=classification.metadata.get("llm_provider", "none"),
                llm_model=classification.metadata.get("llm_model", "none"),
                tokens_used=0,  # TODO: Extract from result
                forwarded_to="",  # Will be filled by routing
                draft_generated=False,  # Will be filled by response generation
                error_occurred=classification.confidence == 0.0,
                error_message=classification.reasoning if classification.confidence == 0.0 else None,
            )
            
            await self.analytics.track_email_processing(metrics)
            
            # Track additional metrics
            await self.analytics.increment_counter(
                "email_classifications_total",
                labels={
                    "category": classification.category.value,
                    "method": method,
                    "priority": classification.priority.value,
                }
            )
            
            await self.analytics.record_histogram(
                "classification_confidence",
                classification.confidence,
                labels={"category": classification.category.value}
            )
            
        except Exception as e:
            logger.error(f"Error tracking classification: {e}") 