"""
Enhanced client manager service for advanced multi-tenant operations.
🏢 Provides intelligent client identification with multiple domain support and fuzzy matching.
"""

import logging
from typing import Dict, List, Optional, Set, Tuple
from functools import lru_cache
from fastapi import Depends

from ..utils.client_loader import (
    get_available_clients,
    load_client_config,
    load_routing_rules,
    ClientLoadError
)
from ..models.client_config import ClientConfig, RoutingRules
from ..utils.domain_resolver import (
    extract_domain_from_email,
    normalize_domain,
    get_domain_hierarchy,
    get_domain_variants,
    DomainMatcher,
    calculate_domain_similarity
)

logger = logging.getLogger(__name__)


class ClientIdentificationResult:
    """Result of client identification with confidence scoring."""
    
    def __init__(self, client_id: Optional[str] = None, confidence: float = 0.0, 
                 method: str = "unknown", domain_used: str = ""):
        self.client_id = client_id
        self.confidence = confidence
        self.method = method
        self.domain_used = domain_used
        self.is_successful = client_id is not None and confidence > 0.5
    
    def __repr__(self):
        return (f"ClientIdentificationResult(client_id='{self.client_id}', "
                f"confidence={self.confidence:.2f}, method='{self.method}')")


class EnhancedClientManager:
    """
    Advanced multi-tenant client configuration manager.
    
    Provides intelligent client identification with multiple domain support,
    fuzzy matching, and confidence scoring. Designed for complex enterprise scenarios.
    """
    
    def __init__(self):
        """Initialize the enhanced client manager."""
        self._clients_cache: Dict[str, ClientConfig] = {}
        self._domain_to_client_cache: Dict[str, str] = {}
        self._client_to_domains_cache: Dict[str, Set[str]] = {}
        self._domain_matcher = DomainMatcher()
        self._initialized = False
        
        # Configuration for identification strategies
        self.confidence_threshold = 0.7
        self.enable_fuzzy_matching = True
        self.enable_hierarchy_matching = True
    
    def _ensure_initialized(self):
        """Ensure client manager is initialized."""
        if not self._initialized:
            self._build_comprehensive_domain_mapping()
            self._initialized = True
    
    def _build_comprehensive_domain_mapping(self):
        """
        Build comprehensive mapping from domains to client IDs with support for:
        - Multiple domains per client
        - Domain aliases and patterns
        - Subdomain hierarchies
        """
        logger.info("Building comprehensive domain to client mapping...")
        self._domain_to_client_cache.clear()
        self._client_to_domains_cache.clear()
        
        available_clients = get_available_clients()
        
        for client_id in available_clients:
            try:
                client_config = load_client_config(client_id)
                client_domains = set()
                
                # Primary domain
                primary_domain = normalize_domain(client_config.domains.primary)
                if primary_domain:
                    self._domain_to_client_cache[primary_domain] = client_id
                    client_domains.add(primary_domain)
                    
                    # Add domain variants for primary domain
                    for variant in get_domain_variants(primary_domain):
                        self._domain_to_client_cache[variant] = client_id
                        client_domains.add(variant)
                
                # Support email domain
                support_email = client_config.domains.support
                support_domain = extract_domain_from_email(support_email)
                if support_domain and support_domain != primary_domain:
                    support_domain = normalize_domain(support_domain)
                    if support_domain:
                        self._domain_to_client_cache[support_domain] = client_id
                        client_domains.add(support_domain)
                        
                        # Add variants for support domain
                        for variant in get_domain_variants(support_domain):
                            self._domain_to_client_cache[variant] = client_id
                            client_domains.add(variant)
                
                # Mailgun domain
                mailgun_domain = normalize_domain(client_config.domains.mailgun)
                if mailgun_domain and mailgun_domain not in [primary_domain, support_domain]:
                    self._domain_to_client_cache[mailgun_domain] = client_id
                    client_domains.add(mailgun_domain)
                    
                    # Add variants for mailgun domain
                    for variant in get_domain_variants(mailgun_domain):
                        self._domain_to_client_cache[variant] = client_id
                        client_domains.add(variant)
                
                # Store client domains for reverse lookup
                self._client_to_domains_cache[client_id] = client_domains
                
                logger.debug(f"Mapped {len(client_domains)} domains for {client_id}: {list(client_domains)[:5]}...")
                
            except ClientLoadError as e:
                logger.error(f"Failed to load client {client_id} during domain mapping: {e}")
        
        # Configure domain matcher with known domains
        all_domains = list(self._domain_to_client_cache.keys())
        for domain in all_domains:
            if '*' not in domain:  # Skip patterns
                self._domain_matcher.add_pattern(f"*.{domain}")
        
        logger.info(f"Comprehensive domain mapping complete: {len(self._domain_to_client_cache)} domains mapped "
                   f"for {len(available_clients)} clients")
    
    def get_available_clients(self) -> List[str]:
        """
        Get list of available client IDs.
        
        Returns:
            List of client IDs
        """
        self._ensure_initialized()
        return get_available_clients()
    
    def get_client_config(self, client_id: str) -> ClientConfig:
        """
        Get client configuration by ID.
        
        Args:
            client_id: Client identifier
            
        Returns:
            ClientConfig object
            
        Raises:
            ClientLoadError: If client cannot be loaded
        """
        self._ensure_initialized()
        
        try:
            return load_client_config(client_id)
        except ClientLoadError as e:
            logger.error(f"Failed to get client config for {client_id}: {e}")
            raise
    
    def get_routing_rules(self, client_id: str) -> RoutingRules:
        """
        Get routing rules for a client.
        
        Args:
            client_id: Client identifier
            
        Returns:
            RoutingRules object
            
        Raises:
            ClientLoadError: If routing rules cannot be loaded
        """
        self._ensure_initialized()
        
        try:
            return load_routing_rules(client_id)
        except ClientLoadError as e:
            logger.error(f"Failed to get routing rules for {client_id}: {e}")
            raise
    
    def get_client_domains(self, client_id: str) -> Set[str]:
        """
        Get all domains associated with a client.
        
        Args:
            client_id: Client identifier
            
        Returns:
            Set of domains for the client
        """
        self._ensure_initialized()
        return self._client_to_domains_cache.get(client_id, set())
    
    def identify_client_by_domain(self, domain: str) -> ClientIdentificationResult:
        """
        Identify client by domain with advanced matching strategies.
        
        Args:
            domain: Email domain (e.g., 'company.com')
            
        Returns:
            ClientIdentificationResult with confidence scoring
        """
        self._ensure_initialized()
        
        domain = normalize_domain(domain)
        if not domain:
            return ClientIdentificationResult(method="invalid_domain")
        
        logger.debug(f"Identifying client for domain: {domain}")
        
        # Strategy 1: Exact domain match
        client_id = self._domain_to_client_cache.get(domain)
        if client_id:
            logger.debug(f"Exact match: {domain} -> {client_id}")
            return ClientIdentificationResult(
                client_id=client_id,
                confidence=1.0,
                method="exact_match",
                domain_used=domain
            )
        
        # Strategy 2: Domain hierarchy matching
        if self.enable_hierarchy_matching:
            hierarchy = get_domain_hierarchy(domain)
            for i, level in enumerate(hierarchy[1:], 1):  # Skip first (exact) match
                client_id = self._domain_to_client_cache.get(level)
                if client_id:
                    confidence = max(0.7, 1.0 - (i * 0.1))  # Decrease confidence by depth
                    logger.debug(f"Hierarchy match: {domain} -> {level} -> {client_id} (confidence: {confidence:.2f})")
                    return ClientIdentificationResult(
                        client_id=client_id,
                        confidence=confidence,
                        method="hierarchy_match",
                        domain_used=level
                    )
        
        # Strategy 3: Fuzzy matching using domain matcher
        if self.enable_fuzzy_matching:
            candidate_domains = list(self._domain_to_client_cache.keys())
            best_match, confidence, method = self._domain_matcher.match_domain(domain, candidate_domains)
            
            if best_match and confidence >= self.confidence_threshold:
                client_id = self._domain_to_client_cache[best_match]
                logger.debug(f"Fuzzy match: {domain} -> {best_match} -> {client_id} "
                           f"(confidence: {confidence:.2f}, method: {method})")
                return ClientIdentificationResult(
                    client_id=client_id,
                    confidence=confidence,
                    method=f"fuzzy_{method}",
                    domain_used=best_match
                )
        
        # Strategy 4: Similarity-based fallback
        all_client_domains = []
        for client_domains in self._client_to_domains_cache.values():
            all_client_domains.extend(client_domains)
        
        best_similarity = 0.0
        best_similar_domain = None
        
        for candidate_domain in all_client_domains:
            similarity = calculate_domain_similarity(domain, candidate_domain)
            if similarity > best_similarity:
                best_similarity = similarity
                best_similar_domain = candidate_domain
        
        if best_similar_domain and best_similarity >= 0.6:
            client_id = self._domain_to_client_cache.get(best_similar_domain)
            if client_id:
                logger.debug(f"Similarity match: {domain} -> {best_similar_domain} -> {client_id} "
                           f"(similarity: {best_similarity:.2f})")
                return ClientIdentificationResult(
                    client_id=client_id,
                    confidence=best_similarity,
                    method="similarity_match",
                    domain_used=best_similar_domain
                )
        
        logger.warning(f"No client found for domain: {domain}")
        return ClientIdentificationResult(method="no_match")
    
    def identify_client_by_email(self, email: str) -> ClientIdentificationResult:
        """
        Identify client by email address with enhanced matching.
        
        Args:
            email: Email address (e.g., 'user@company.com')
            
        Returns:
            ClientIdentificationResult with confidence scoring
        """
        domain = extract_domain_from_email(email)
        if not domain:
            logger.warning(f"Invalid email format: {email}")
            return ClientIdentificationResult(method="invalid_email")
        
        result = self.identify_client_by_domain(domain)
        logger.debug(f"Email identification for {email}: {result}")
        return result
    
    def identify_client_by_email_simple(self, email: str) -> Optional[str]:
        """
        Simple client identification for backward compatibility.
        
        Args:
            email: Email address
            
        Returns:
            Client ID if found with sufficient confidence, None otherwise
        """
        result = self.identify_client_by_email(email)
        return result.client_id if result.is_successful else None
    
    def identify_client_by_domain_simple(self, domain: str) -> Optional[str]:
        """
        Simple domain identification for backward compatibility.
        
        Args:
            domain: Domain string
            
        Returns:
            Client ID if found with sufficient confidence, None otherwise
        """
        result = self.identify_client_by_domain(domain)
        return result.client_id if result.is_successful else None
    
    def get_routing_destination(self, client_id: str, category: str) -> Optional[str]:
        """
        Get routing destination email for a category.
        
        Args:
            client_id: Client identifier
            category: Email category (e.g., 'support', 'billing')
            
        Returns:
            Destination email address if found, None otherwise
        """
        try:
            routing_rules = self.get_routing_rules(client_id)
            destination = routing_rules.routing.get(category)
            
            if destination:
                logger.debug(f"Routing {category} for {client_id} to {destination}")
                return destination
            
            # Try backup routing
            if routing_rules.backup_routing:
                backup_destination = routing_rules.backup_routing.get(category)
                if backup_destination:
                    logger.info(f"Using backup routing for {category} -> {backup_destination}")
                    return backup_destination
            
            # Fallback to general if category not found
            general_destination = routing_rules.routing.get('general')
            if general_destination:
                logger.info(f"Fallback routing {category} -> general for {client_id}")
                return general_destination
                
            logger.error(f"No routing destination found for {category} in {client_id}")
            return None
            
        except ClientLoadError as e:
            logger.error(f"Failed to get routing destination: {e}")
            return None
    
    def get_response_time(self, client_id: str, category: str) -> str:
        """
        Get expected response time for a category.
        
        Args:
            client_id: Client identifier
            category: Email category
            
        Returns:
            Response time string (e.g., 'within 4 hours')
        """
        try:
            client_config = self.get_client_config(client_id)
            
            # Check if category has specific response time
            if hasattr(client_config.response_times, category):
                return getattr(client_config.response_times, category)
            
            # Fallback to general
            return client_config.response_times.general
            
        except ClientLoadError as e:
            logger.error(f"Failed to get response time: {e}")
            return "within 24 hours"  # Safe fallback
    
    def find_similar_clients(self, domain: str, limit: int = 5) -> List[Tuple[str, float]]:
        """
        Find clients with similar domains.
        
        Args:
            domain: Domain to find similar clients for
            limit: Maximum number of results to return
            
        Returns:
            List of tuples (client_id, similarity_score)
        """
        self._ensure_initialized()
        
        domain = normalize_domain(domain)
        if not domain:
            return []
        
        client_similarities = []
        
        for client_id, client_domains in self._client_to_domains_cache.items():
            max_similarity = 0.0
            
            for client_domain in client_domains:
                similarity = calculate_domain_similarity(domain, client_domain)
                max_similarity = max(max_similarity, similarity)
            
            if max_similarity > 0.3:  # Only include reasonably similar clients
                client_similarities.append((client_id, max_similarity))
        
        # Sort by similarity and return top results
        client_similarities.sort(key=lambda x: x[1], reverse=True)
        return client_similarities[:limit]
    
    def add_domain_alias(self, alias_domain: str, canonical_domain: str):
        """
        Add domain alias for better matching.
        
        Args:
            alias_domain: Alias domain
            canonical_domain: Canonical domain to map to
        """
        self._domain_matcher.add_alias(alias_domain, canonical_domain)
        logger.info(f"Added domain alias: {alias_domain} -> {canonical_domain}")
    
    def refresh_client(self, client_id: str):
        """
        Refresh configuration for a specific client.
        
        Args:
            client_id: Client identifier to refresh
        """
        try:
            # Force reload from disk
            load_client_config(client_id, force_reload=True)
            load_routing_rules(client_id, force_reload=True)
            
            # Rebuild domain mapping to pick up changes
            self._build_comprehensive_domain_mapping()
            
            logger.info(f"Refreshed configuration for client {client_id}")
            
        except ClientLoadError as e:
            logger.error(f"Failed to refresh client {client_id}: {e}")
    
    def refresh_all_clients(self):
        """Refresh configurations for all clients."""
        logger.info("Refreshing all client configurations...")
        
        available_clients = get_available_clients()
        for client_id in available_clients:
            try:
                self.refresh_client(client_id)
            except Exception as e:
                logger.error(f"Failed to refresh client {client_id}: {e}")
        
        logger.info("Completed refreshing all client configurations")
    
    def validate_client_setup(self, client_id: str) -> bool:
        """
        Validate that a client is properly configured.
        
        Args:
            client_id: Client identifier to validate
            
        Returns:
            True if client is valid, False otherwise
        """
        try:
            # Test loading all required configurations
            client_config = self.get_client_config(client_id)
            routing_rules = self.get_routing_rules(client_id)
            
            # Basic validation checks
            if not client_config.client.id == client_id:
                logger.error(f"Client ID mismatch in config: {client_config.client.id} != {client_id}")
                return False
            
            if not routing_rules.routing:
                logger.error(f"No routing rules defined for {client_id}")
                return False
            
            # Check required routing categories
            required_categories = ['support', 'billing', 'sales', 'general']
            for category in required_categories:
                if category not in routing_rules.routing:
                    logger.warning(f"Missing routing rule for {category} in {client_id}")
            
            # Validate domains
            domains = self.get_client_domains(client_id)
            if not domains:
                logger.error(f"No domains configured for {client_id}")
                return False
            
            logger.info(f"Client validation passed for {client_id}")
            return True
            
        except Exception as e:
            logger.error(f"Client validation failed for {client_id}: {e}")
            return False
    
    def get_client_summary(self, client_id: str) -> Dict:
        """
        Get comprehensive summary of client configuration.
        
        Args:
            client_id: Client identifier
            
        Returns:
            Dictionary with client summary information
        """
        try:
            client_config = self.get_client_config(client_id)
            routing_rules = self.get_routing_rules(client_id)
            domains = self.get_client_domains(client_id)
            
            return {
                'client_id': client_id,
                'name': client_config.client.name,
                'industry': client_config.client.industry,
                'status': client_config.client.status,
                'domains': list(domains),
                'primary_domain': client_config.domains.primary,
                'routing_categories': list(routing_rules.routing.keys()),
                'total_domains': len(domains),
                'settings': {
                    'ai_classification_enabled': client_config.settings.ai_classification_enabled,
                    'auto_reply_enabled': client_config.settings.auto_reply_enabled,
                    'team_forwarding_enabled': client_config.settings.team_forwarding_enabled,
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get client summary for {client_id}: {e}")
            return {'client_id': client_id, 'error': str(e)}


# Create alias for backward compatibility
ClientManager = EnhancedClientManager


def get_client_manager():
    """Dependency injection function for ClientManager."""
    return EnhancedClientManager() 