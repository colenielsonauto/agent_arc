"""
Dynamic email routing engine using client-specific rules.
📤 Multi-tenant email routing with escalation and special rules.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, time, timedelta
import pytz

from ..services.client_manager import ClientManager
from ..models.client_config import ClientConfig, RoutingRules
from ..utils.domain_resolver import extract_domain_from_email

logger = logging.getLogger(__name__)


class RoutingEngine:
    """
    Multi-tenant email routing engine.
    
    Routes emails to appropriate team members based on client-specific
    rules, escalation policies, and business hours.
    """
    
    def __init__(self, client_manager: ClientManager):
        """
        Initialize routing engine.
        
        Args:
            client_manager: ClientManager instance for client operations
        """
        self.client_manager = client_manager
    
    def route_email(self, client_id: str, classification: Dict[str, Any], 
                   email_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Route email to appropriate team member.
        
        Args:
            client_id: Client identifier
            classification: Email classification result
            email_data: Optional email data for context
            
        Returns:
            Routing decision with destination, escalation info, etc.
        """
        try:
            routing_rules = self.client_manager.get_routing_rules(client_id)
            client_config = self.client_manager.get_client_config(client_id)
            
            category = classification.get('category', 'general')
            confidence = classification.get('confidence', 0.5)
            
            # Check for immediate escalation triggers
            escalation_result = self._check_immediate_escalation(
                client_id, classification, email_data, routing_rules
            )
            if escalation_result:
                logger.info(f"🚨 Immediate escalation triggered for {client_id}: {escalation_result['reason']}")
                return escalation_result
            
            # Get primary routing destination
            primary_destination = self._get_primary_destination(routing_rules, category)
            
            if not primary_destination:
                # Try backup routing
                backup_destination = self._get_backup_destination(routing_rules, category)
                if backup_destination:
                    logger.warning(f"Using backup routing for {category} -> {backup_destination}")
                    primary_destination = backup_destination
                else:
                    # Final fallback to general
                    primary_destination = routing_rules.routing.get('general')
                    if not primary_destination:
                        logger.error(f"No routing destination found for {client_id}, using primary contact")
                        primary_destination = client_config.contacts.primary_contact
            
            # Check business hours and route accordingly
            final_destination = self._apply_business_hours_routing(
                client_id, primary_destination, routing_rules, client_config
            )
            
            # Determine escalation schedule
            escalation_schedule = self._get_escalation_schedule(
                client_id, category, routing_rules, classification
            )
            
            # Build routing result
            routing_result = {
                'client_id': client_id,
                'category': category,
                'primary_destination': final_destination,
                'backup_destinations': self._get_backup_destinations(routing_rules, category),
                'escalation_schedule': escalation_schedule,
                'business_hours_applied': final_destination != primary_destination,
                'confidence_level': self._get_confidence_level(confidence),
                'special_handling': self._get_special_handling(client_id, email_data, routing_rules),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            logger.info(f"📍 Routed {category} email for {client_id} to {final_destination}")
            return routing_result
            
        except Exception as e:
            logger.error(f"Routing failed for {client_id}: {e}")
            return self._get_fallback_routing(client_id, classification)
    
    def _check_immediate_escalation(self, client_id: str, classification: Dict[str, Any],
                                  email_data: Dict[str, Any], routing_rules: RoutingRules) -> Optional[Dict[str, Any]]:
        """
        Check if email should be immediately escalated.
        
        Args:
            client_id: Client identifier
            classification: Email classification result
            email_data: Email data for context checks
            routing_rules: Client routing rules
            
        Returns:
            Escalation routing if triggered, None otherwise
        """
        if not routing_rules.escalation or not routing_rules.escalation.keyword_based:
            return None
        
        # Check keyword-based escalation
        if email_data:
            subject = email_data.get('subject', '').lower()
            body = (email_data.get('stripped_text') or email_data.get('body_text', '')).lower()
            text = f"{subject} {body}"
            
            for keyword, escalation_destination in routing_rules.escalation.keyword_based.items():
                if keyword.lower() in text:
                    return {
                        'primary_destination': escalation_destination,
                        'escalation_triggered': True,
                        'escalation_type': 'keyword',
                        'escalation_reason': f"Keyword '{keyword}' detected",
                        'reason': f"Immediate escalation: keyword '{keyword}' detected",
                        'priority': 'urgent',
                        'timestamp': datetime.utcnow().isoformat()
                    }
        
        # Check VIP domain escalation
        if email_data and routing_rules.special_rules:
            sender = email_data.get('from', '')
            if sender:
                sender_domain = extract_domain_from_email(sender)
                if sender_domain and sender_domain in routing_rules.special_rules.vip_domains:
                    vip_destination = routing_rules.special_rules.vip_route_to
                    if vip_destination:
                        return {
                            'primary_destination': vip_destination,
                            'escalation_triggered': True,
                            'escalation_type': 'vip_domain',
                            'escalation_reason': f"VIP domain: {sender_domain}",
                            'reason': f"VIP routing: {sender_domain}",
                            'priority': 'high',
                            'timestamp': datetime.utcnow().isoformat()
                        }
        
        # Check confidence-based escalation
        confidence = classification.get('confidence', 1.0)
        if confidence < 0.3:  # Very low confidence
            try:
                client_config = self.client_manager.get_client_config(client_id)
                escalation_contact = client_config.contacts.escalation_contact
                return {
                    'primary_destination': escalation_contact,
                    'escalation_triggered': True,
                    'escalation_type': 'low_confidence',
                    'escalation_reason': f"Low classification confidence: {confidence:.2f}",
                    'reason': f"Low confidence escalation: {confidence:.2f}",
                    'priority': 'medium',
                    'timestamp': datetime.utcnow().isoformat()
                }
            except Exception as e:
                logger.warning(f"Failed to get escalation contact for low confidence: {e}")
        
        return None
    
    def _get_primary_destination(self, routing_rules: RoutingRules, category: str) -> Optional[str]:
        """
        Get primary routing destination for category.
        
        Args:
            routing_rules: Client routing rules
            category: Email category
            
        Returns:
            Primary destination email if found
        """
        return routing_rules.routing.get(category)
    
    def _get_backup_destination(self, routing_rules: RoutingRules, category: str) -> Optional[str]:
        """
        Get backup routing destination for category.
        
        Args:
            routing_rules: Client routing rules
            category: Email category
            
        Returns:
            Backup destination email if found
        """
        if routing_rules.backup_routing:
            return routing_rules.backup_routing.get(category)
        return None
    
    def _get_backup_destinations(self, routing_rules: RoutingRules, category: str) -> List[str]:
        """
        Get list of backup destinations for category.
        
        Args:
            routing_rules: Client routing rules
            category: Email category
            
        Returns:
            List of backup destination emails
        """
        backups = []
        
        # Add backup routing destination
        backup = self._get_backup_destination(routing_rules, category)
        if backup:
            backups.append(backup)
        
        # Add general routing as ultimate backup
        general = routing_rules.routing.get('general')
        if general and general not in backups:
            backups.append(general)
        
        return backups
    
    def _apply_business_hours_routing(self, client_id: str, primary_destination: str,
                                    routing_rules: RoutingRules, client_config: ClientConfig) -> str:
        """
        Apply business hours routing rules.
        
        Args:
            client_id: Client identifier
            primary_destination: Primary routing destination
            routing_rules: Client routing rules
            client_config: Client configuration
            
        Returns:
            Final destination after business hours consideration
        """
        try:
            # Check if we're in business hours
            if self._is_business_hours(client_config):
                # During business hours, use primary destination
                return primary_destination
            
            # Outside business hours, check for special routing
            if routing_rules.special_rules:
                # Check if it's weekend
                now = datetime.now(pytz.timezone(client_config.client.timezone))
                if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
                    weekend_destination = routing_rules.special_rules.weekend_route_to
                    if weekend_destination:
                        logger.info(f"Applying weekend routing: {weekend_destination}")
                        return weekend_destination
                
                # After hours routing
                after_hours_destination = routing_rules.special_rules.after_hours_route_to
                if after_hours_destination:
                    logger.info(f"Applying after-hours routing: {after_hours_destination}")
                    return after_hours_destination
            
            # No special routing configured, use primary destination
            return primary_destination
            
        except Exception as e:
            logger.warning(f"Failed to apply business hours routing for {client_id}: {e}")
            return primary_destination
    
    def _is_business_hours(self, client_config: ClientConfig) -> bool:
        """
        Check if current time is within business hours.
        
        Args:
            client_config: Client configuration
            
        Returns:
            True if within business hours, False otherwise
        """
        try:
            client_tz = pytz.timezone(client_config.client.timezone)
            now = datetime.now(client_tz)
            
            # Check if it's a work day (assuming Monday=0, Sunday=6)
            # For now, assume Monday-Friday are work days
            if now.weekday() >= 5:  # Weekend
                return False
            
            # Parse business hours (e.g., "9-17")
            business_hours = client_config.client.business_hours
            if '-' in business_hours:
                start_hour, end_hour = business_hours.split('-')
                start_time = time(int(start_hour), 0)
                end_time = time(int(end_hour), 0)
                
                current_time = now.time()
                return start_time <= current_time <= end_time
            
            # If we can't parse business hours, assume we're in business hours
            return True
            
        except Exception as e:
            logger.warning(f"Failed to check business hours: {e}")
            return True  # Default to business hours if check fails
    
    def _get_escalation_schedule(self, client_id: str, category: str, routing_rules: RoutingRules,
                               classification: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get escalation schedule for category.
        
        Args:
            client_id: Client identifier
            category: Email category
            routing_rules: Client routing rules
            classification: Classification result
            
        Returns:
            List of escalation steps with timing and destinations
        """
        escalation_schedule = []
        
        try:
            if not routing_rules.escalation or not routing_rules.escalation.time_based:
                return escalation_schedule
            
            category_escalation = getattr(routing_rules.escalation.time_based, category, None)
            if not category_escalation:
                return escalation_schedule
            
            for i, rule in enumerate(category_escalation):
                escalation_schedule.append({
                    'step': i + 1,
                    'hours_after': rule.hours,
                    'escalate_to': rule.escalate_to,
                    'escalation_time': self._calculate_escalation_time(rule.hours),
                    'category': category
                })
            
        except Exception as e:
            logger.warning(f"Failed to get escalation schedule for {client_id}: {e}")
        
        return escalation_schedule
    
    def _calculate_escalation_time(self, hours_after: int) -> str:
        """
        Calculate escalation time from now.
        
        Args:
            hours_after: Hours after initial email
            
        Returns:
            ISO timestamp for escalation time
        """
        escalation_time = datetime.utcnow() + datetime.timedelta(hours=hours_after)
        return escalation_time.isoformat()
    
    def _get_confidence_level(self, confidence: float) -> str:
        """
        Get confidence level category.
        
        Args:
            confidence: Confidence score (0-1)
            
        Returns:
            Confidence level string
        """
        if confidence >= 0.9:
            return 'very_high'
        elif confidence >= 0.7:
            return 'high'
        elif confidence >= 0.5:
            return 'medium'
        elif confidence >= 0.3:
            return 'low'
        else:
            return 'very_low'
    
    def _get_special_handling(self, client_id: str, email_data: Dict[str, Any],
                            routing_rules: RoutingRules) -> List[str]:
        """
        Get special handling flags for email.
        
        Args:
            client_id: Client identifier
            email_data: Email data
            routing_rules: Client routing rules
            
        Returns:
            List of special handling flags
        """
        flags = []
        
        try:
            if not email_data or not routing_rules.special_rules:
                return flags
            
            # Check VIP sender
            sender = email_data.get('from', '')
            if sender:
                sender_domain = extract_domain_from_email(sender)
                if sender_domain and sender_domain in routing_rules.special_rules.vip_domains:
                    flags.append('vip_sender')
            
            # Check for urgent keywords in subject/body
            subject = email_data.get('subject', '').lower()
            body = (email_data.get('stripped_text') or email_data.get('body_text', '')).lower()
            text = f"{subject} {body}"
            
            urgent_keywords = ['urgent', 'emergency', 'critical', 'asap', 'immediate']
            if any(keyword in text for keyword in urgent_keywords):
                flags.append('urgent_keywords')
            
            # Check for complaint indicators
            complaint_keywords = ['complaint', 'dissatisfied', 'unhappy', 'terrible', 'awful', 'worst']
            if any(keyword in text for keyword in complaint_keywords):
                flags.append('complaint_indicators')
            
        except Exception as e:
            logger.warning(f"Failed to get special handling for {client_id}: {e}")
        
        return flags
    
    def _get_fallback_routing(self, client_id: str, classification: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get fallback routing when normal routing fails.
        
        Args:
            client_id: Client identifier
            classification: Classification result
            
        Returns:
            Fallback routing result
        """
        try:
            client_config = self.client_manager.get_client_config(client_id)
            primary_contact = client_config.contacts.primary_contact
            
            return {
                'client_id': client_id,
                'category': classification.get('category', 'general'),
                'primary_destination': primary_contact,
                'backup_destinations': [client_config.contacts.escalation_contact],
                'escalation_schedule': [],
                'business_hours_applied': False,
                'confidence_level': 'unknown',
                'special_handling': ['fallback_routing'],
                'error': 'Normal routing failed, using fallback',
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Fallback routing failed for {client_id}: {e}")
            return {
                'client_id': client_id,
                'category': classification.get('category', 'general'),
                'primary_destination': 'admin@example.com',  # Hard fallback
                'backup_destinations': [],
                'escalation_schedule': [],
                'business_hours_applied': False,
                'confidence_level': 'unknown',
                'special_handling': ['hard_fallback'],
                'error': 'All routing methods failed',
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def get_routing_analytics(self, client_id: str, time_period_hours: int = 24) -> Dict[str, Any]:
        """
        Get routing analytics for a client.
        
        Args:
            client_id: Client identifier
            time_period_hours: Time period for analytics
            
        Returns:
            Routing analytics data
        """
        # TODO: Implement routing analytics
        # This would track routing decisions, escalations, response times, etc.
        return {
            'client_id': client_id,
            'time_period_hours': time_period_hours,
            'total_emails': 0,
            'routing_breakdown': {},
            'escalations': 0,
            'avg_confidence': 0.0,
            'special_handling_count': 0
        }


def get_routing_engine(client_manager: ClientManager = None):
    """Dependency injection function for RoutingEngine."""
    if client_manager is None:
        from .client_manager import get_client_manager
        client_manager = get_client_manager()
    
    return RoutingEngine(client_manager) 