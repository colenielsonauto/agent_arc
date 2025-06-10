"""
Template engine for AI prompt composition with client-specific context.
🎨 Composes prompts by injecting client data into template files.
"""

import logging
import re
from typing import Dict, Any, Optional
from string import Template

from ..services.client_manager import ClientManager
from ..utils.client_loader import load_ai_prompt, load_fallback_responses, ClientLoadError
from ..models.client_config import ClientConfig

logger = logging.getLogger(__name__)


class TemplateEngine:
    """
    AI prompt template engine with client-specific data injection.
    
    Loads prompt templates and injects client configuration data
    to create personalized AI prompts for each client.
    """
    
    def __init__(self, client_manager: ClientManager):
        """
        Initialize template engine.
        
        Args:
            client_manager: ClientManager instance for accessing client data
        """
        self.client_manager = client_manager
        self._template_cache: Dict[str, str] = {}
    
    def _load_template(self, client_id: str, template_type: str) -> str:
        """
        Load prompt template for a client.
        
        Args:
            client_id: Client identifier
            template_type: Type of template ('classification', 'acknowledgment', 'team-analysis')
            
        Returns:
            Template content as string
            
        Raises:
            ClientLoadError: If template cannot be loaded
        """
        cache_key = f"{client_id}_{template_type}"
        
        # Check cache first
        if cache_key in self._template_cache:
            return self._template_cache[cache_key]
        
        try:
            template_content = load_ai_prompt(client_id, template_type)
            self._template_cache[cache_key] = template_content
            return template_content
            
        except ClientLoadError as e:
            logger.error(f"Failed to load {template_type} template for {client_id}: {e}")
            raise
    
    def _prepare_template_context(self, client_id: str, email_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Prepare context data for template injection.
        
        Args:
            client_id: Client identifier
            email_data: Optional email data for context
            
        Returns:
            Dictionary of context data for template injection
        """
        try:
            client_config = self.client_manager.get_client_config(client_id)
            routing_rules = self.client_manager.get_routing_rules(client_id)
            
            # Base context with client configuration
            context = {
                'client': {
                    'id': client_config.client.id,
                    'name': client_config.client.name,
                    'industry': client_config.client.industry,
                    'timezone': client_config.client.timezone,
                    'business_hours': client_config.client.business_hours,
                },
                'branding': {
                    'company_name': client_config.branding.company_name,
                    'email_signature': client_config.branding.email_signature,
                    'primary_color': client_config.branding.primary_color,
                    'secondary_color': client_config.branding.secondary_color,
                },
                'response_times': {
                    'support': client_config.response_times.support,
                    'billing': client_config.response_times.billing,
                    'sales': client_config.response_times.sales,
                    'general': client_config.response_times.general,
                },
                'routing': routing_rules.routing,
                'domains': {
                    'primary': client_config.domains.primary,
                    'support': client_config.domains.support,
                    'mailgun': client_config.domains.mailgun,
                }
            }
            
            # Add email data if provided
            if email_data:
                context.update({
                    'sender': email_data.get('from', ''),
                    'subject': email_data.get('subject', ''),
                    'body': email_data.get('stripped_text') or email_data.get('body_text', ''),
                    'recipient': email_data.get('to', ''),
                })
            
            return context
            
        except Exception as e:
            logger.error(f"Failed to prepare template context for {client_id}: {e}")
            raise
    
    def _inject_template_variables(self, template: str, context: Dict[str, Any]) -> str:
        """
        Inject variables into template using both {{}} and {} syntax.
        
        Args:
            template: Template string with variables
            context: Context data for injection
            
        Returns:
            Template with variables injected
        """
        try:
            # First pass: Handle {{client.name}} style variables
            def replace_double_braces(match):
                var_path = match.group(1)
                return self._get_nested_value(context, var_path)
            
            # Replace {{variable.path}} patterns
            template = re.sub(r'\{\{([^}]+)\}\}', replace_double_braces, template)
            
            # Second pass: Handle {variable} style variables using string.Template
            template_obj = Template(template)
            
            # Flatten context for simple variable substitution
            flat_context = self._flatten_context(context)
            
            # Use safe_substitute to avoid KeyError for missing variables
            result = template_obj.safe_substitute(flat_context)
            
            return result
            
        except Exception as e:
            logger.error(f"Error injecting template variables: {e}")
            return template  # Return original template if injection fails
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> str:
        """
        Get nested value from dictionary using dot notation.
        
        Args:
            data: Dictionary to search
            path: Dot-separated path (e.g., 'client.name')
            
        Returns:
            Value as string, or original path if not found
        """
        try:
            keys = path.split('.')
            value = data
            
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    # Return original path if not found
                    return f"{{{{{path}}}}}"
            
            return str(value)
            
        except Exception:
            return f"{{{{{path}}}}}"
    
    def _flatten_context(self, context: Dict[str, Any], prefix: str = '') -> Dict[str, str]:
        """
        Flatten nested dictionary for simple template substitution.
        
        Args:
            context: Nested dictionary to flatten
            prefix: Prefix for keys
            
        Returns:
            Flattened dictionary with string values
        """
        flat = {}
        
        for key, value in context.items():
            new_key = f"{prefix}{key}" if prefix else key
            
            if isinstance(value, dict):
                flat.update(self._flatten_context(value, f"{new_key}_"))
            else:
                flat[new_key] = str(value)
        
        return flat
    
    def compose_classification_prompt(self, client_id: str, email_data: Dict[str, Any]) -> str:
        """
        Compose classification prompt for a client.
        
        Args:
            client_id: Client identifier
            email_data: Email data from webhook
            
        Returns:
            Composed classification prompt
        """
        try:
            template = self._load_template(client_id, 'classification')
            context = self._prepare_template_context(client_id, email_data)
            
            prompt = self._inject_template_variables(template, context)
            
            logger.debug(f"Composed classification prompt for {client_id} ({len(prompt)} chars)")
            return prompt
            
        except Exception as e:
            logger.error(f"Failed to compose classification prompt for {client_id}: {e}")
            
            # Fallback to basic classification prompt
            return self._get_fallback_classification_prompt(email_data)
    
    def compose_acknowledgment_prompt(self, client_id: str, email_data: Dict[str, Any], 
                                    classification: Dict[str, Any]) -> str:
        """
        Compose acknowledgment prompt for a client.
        
        Args:
            client_id: Client identifier
            email_data: Email data from webhook
            classification: Email classification result
            
        Returns:
            Composed acknowledgment prompt
        """
        try:
            template = self._load_template(client_id, 'acknowledgment')
            context = self._prepare_template_context(client_id, email_data)
            
            # Add classification context
            context.update({
                'category': classification.get('category', 'general'),
                'priority': classification.get('priority', 'medium'),
                'confidence': classification.get('confidence', 0.5),
            })
            
            prompt = self._inject_template_variables(template, context)
            
            logger.debug(f"Composed acknowledgment prompt for {client_id} ({len(prompt)} chars)")
            return prompt
            
        except Exception as e:
            logger.error(f"Failed to compose acknowledgment prompt for {client_id}: {e}")
            
            # Fallback to basic acknowledgment prompt
            return self._get_fallback_acknowledgment_prompt(client_id, classification)
    
    def compose_team_analysis_prompt(self, client_id: str, email_data: Dict[str, Any], 
                                   classification: Dict[str, Any]) -> str:
        """
        Compose team analysis prompt for a client.
        
        Args:
            client_id: Client identifier
            email_data: Email data from webhook
            classification: Email classification result
            
        Returns:
            Composed team analysis prompt
        """
        try:
            template = self._load_template(client_id, 'team-analysis')
            context = self._prepare_template_context(client_id, email_data)
            
            # Add classification and routing context
            routing_destination = self.client_manager.get_routing_destination(
                client_id, classification.get('category', 'general')
            )
            
            context.update({
                'category': classification.get('category', 'general'),
                'priority': classification.get('priority', 'medium'),
                'confidence': classification.get('confidence', 0.5),
                'reasoning': classification.get('reasoning', ''),
                'assigned_to': routing_destination,
            })
            
            prompt = self._inject_template_variables(template, context)
            
            logger.debug(f"Composed team analysis prompt for {client_id} ({len(prompt)} chars)")
            return prompt
            
        except Exception as e:
            logger.error(f"Failed to compose team analysis prompt for {client_id}: {e}")
            
            # Fallback to basic team analysis prompt
            return self._get_fallback_team_analysis_prompt(client_id, classification)
    
    def get_fallback_response(self, client_id: str, response_type: str, category: str = 'general') -> str:
        """
        Get fallback response when AI services fail.
        
        Args:
            client_id: Client identifier
            response_type: Type of response ('customer_acknowledgments', 'team_analysis')
            category: Email category
            
        Returns:
            Fallback response string
        """
        try:
            fallback_data = load_fallback_responses(client_id)
            
            if response_type in fallback_data and category in fallback_data[response_type]:
                template = fallback_data[response_type][category]
                context = self._prepare_template_context(client_id)
                return self._inject_template_variables(template, context)
            
            # Fallback to general if category not found
            if response_type in fallback_data and 'general' in fallback_data[response_type]:
                template = fallback_data[response_type]['general']
                context = self._prepare_template_context(client_id)
                return self._inject_template_variables(template, context)
                
        except Exception as e:
            logger.error(f"Failed to get fallback response for {client_id}: {e}")
        
        # Hard fallback
        return self._get_hard_fallback_response(response_type, category)
    
    def _get_fallback_classification_prompt(self, email_data: Dict[str, Any]) -> str:
        """Get basic fallback classification prompt."""
        return f"""
You are an intelligent email classifier. Analyze this email and classify it:

Categories:
- billing: Payment issues, invoices, account billing
- support: Technical problems, how-to questions, product issues  
- sales: Pricing inquiries, product demos, new business
- general: Everything else

Email:
Subject: {email_data.get('subject', '')}
Body: {email_data.get('stripped_text') or email_data.get('body_text', '')}

Respond in JSON format:
{{
    "category": "one of the categories above",
    "confidence": 0.95,
    "reasoning": "Brief explanation",
    "suggested_actions": ["action1", "action2"]
}}
"""
    
    def _get_fallback_acknowledgment_prompt(self, client_id: str, classification: Dict[str, Any]) -> str:
        """Get basic fallback acknowledgment prompt."""
        category = classification.get('category', 'general')
        return f"""
Generate a brief professional acknowledgment for a {category} inquiry.
Keep it under 150 words, thank the customer, and mention we'll respond within 24 hours.
"""
    
    def _get_fallback_team_analysis_prompt(self, client_id: str, classification: Dict[str, Any]) -> str:
        """Get basic fallback team analysis prompt."""
        category = classification.get('category', 'general')
        return f"""
Email classified as {category.upper()} inquiry (fallback classification).
Please review the original message and respond accordingly.
"""
    
    def _get_hard_fallback_response(self, response_type: str, category: str) -> str:
        """Get hard-coded fallback response when all else fails."""
        if response_type == 'customer_acknowledgments':
            return f"Thank you for contacting us. We've received your {category} inquiry and will respond within 24 hours."
        elif response_type == 'team_analysis':
            return f"Email classified as {category.upper()} inquiry. Please review and respond accordingly."
        else:
            return "Email received and being processed."
    
    def clear_cache(self):
        """Clear template cache."""
        self._template_cache.clear()
        logger.info("Template cache cleared") 