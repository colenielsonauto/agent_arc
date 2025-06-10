"""
Enhanced domain resolution utilities for multi-tenant client identification.
🌐 Advanced domain handling with fuzzy matching and pattern support.
"""

import logging
import re
from typing import Optional, List, Dict, Tuple
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def extract_domain_from_email(email: str) -> Optional[str]:
    """
    Extract domain from email address with enhanced validation.
    
    Args:
        email: Email address (e.g., 'user@company.com')
        
    Returns:
        Domain string if valid, None otherwise
        
    Examples:
        >>> extract_domain_from_email('user@company.com')
        'company.com'
        >>> extract_domain_from_email('support@sub.company.com')
        'sub.company.com'
    """
    if not email or '@' not in email:
        logger.warning(f"Invalid email format: {email}")
        return None
    
    try:
        # Split email and get parts
        parts = email.split('@')
        if len(parts) != 2:
            logger.warning(f"Invalid email format: {email}")
            return None
        
        local_part, domain = parts
        
        # Check if local part is empty (like @domain.com)
        if not local_part.strip():
            logger.warning(f"Invalid email format: {email}")
            return None
        
        # Process domain part
        domain = domain.lower().strip()
        
        # Basic domain validation
        if not domain or '.' not in domain:
            logger.warning(f"Invalid domain in email: {email}")
            return None
        
        # Remove any trailing periods
        domain = domain.rstrip('.')
        
        # Validate domain format
        if not is_valid_domain_format(domain):
            logger.warning(f"Invalid domain format in email: {email}")
            return None
        
        logger.debug(f"Extracted domain '{domain}' from email '{email}'")
        return domain
        
    except Exception as e:
        logger.error(f"Error extracting domain from email '{email}': {e}")
        return None


def extract_domain_from_url(url: str) -> Optional[str]:
    """
    Extract domain from URL with enhanced validation.
    
    Args:
        url: URL string (e.g., 'https://company.com/path')
        
    Returns:
        Domain string if valid, None otherwise
        
    Examples:
        >>> extract_domain_from_url('https://company.com/path')
        'company.com'
        >>> extract_domain_from_url('http://sub.company.com')
        'sub.company.com'
    """
    if not url:
        return None
    
    try:
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            url = f'https://{url}'
        
        # Parse URL and extract netloc (domain)
        parsed = urlparse(url)
        domain = parsed.netloc.lower().strip()
        
        # Remove port if present
        if ':' in domain:
            domain = domain.split(':')[0]
        
        # Remove www prefix if present
        if domain.startswith('www.'):
            domain = domain[4:]
        
        if not domain or '.' not in domain:
            logger.warning(f"Invalid domain in URL: {url}")
            return None
        
        # Validate domain format
        if not is_valid_domain_format(domain):
            logger.warning(f"Invalid domain format in URL: {url}")
            return None
        
        logger.debug(f"Extracted domain '{domain}' from URL '{url}'")
        return domain
        
    except Exception as e:
        logger.error(f"Error extracting domain from URL '{url}': {e}")
        return None


def normalize_domain(domain: str) -> Optional[str]:
    """
    Normalize domain name for consistent matching.
    
    Args:
        domain: Domain string to normalize
        
    Returns:
        Normalized domain string if valid, None otherwise
        
    Examples:
        >>> normalize_domain('Company.COM')
        'company.com'
        >>> normalize_domain('www.company.com')
        'company.com'
    """
    if not domain:
        return None
    
    try:
        # Convert to lowercase and strip whitespace
        domain = domain.lower().strip()
        
        # Remove protocol if present
        if domain.startswith(('http://', 'https://')):
            domain = extract_domain_from_url(domain)
            if not domain:
                return None
        
        # Remove www prefix
        if domain.startswith('www.'):
            domain = domain[4:]
        
        # Remove trailing periods
        domain = domain.rstrip('.')
        
        # Basic validation
        if not domain or '.' not in domain:
            logger.warning(f"Invalid domain format: {domain}")
            return None
        
        # Validate domain format
        if not is_valid_domain_format(domain):
            logger.warning(f"Invalid domain pattern: {domain}")
            return None
        
        logger.debug(f"Normalized domain: '{domain}'")
        return domain
        
    except Exception as e:
        logger.error(f"Error normalizing domain '{domain}': {e}")
        return None


def is_valid_domain_format(domain: str) -> bool:
    """
    Validate domain format using regex pattern.
    
    Args:
        domain: Domain string to validate
        
    Returns:
        True if domain format is valid, False otherwise
    """
    if not domain:
        return False
    
    # Enhanced domain pattern supporting unicode domains
    domain_pattern = re.compile(
        r'^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?(\.[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?)*$'
    )
    
    return bool(domain_pattern.match(domain))


def get_parent_domain(domain: str) -> Optional[str]:
    """
    Get parent domain from subdomain.
    
    Args:
        domain: Domain string (e.g., 'support.company.com')
        
    Returns:
        Parent domain if applicable, None otherwise
        
    Examples:
        >>> get_parent_domain('support.company.com')
        'company.com'
        >>> get_parent_domain('api.v1.company.com')
        'company.com'
        >>> get_parent_domain('company.com')
        None  # Already a parent domain
    """
    if not domain:
        return None
    
    try:
        domain = normalize_domain(domain)
        if not domain:
            return None
        
        parts = domain.split('.')
        
        # If only 2 parts (e.g., 'company.com'), it's already a parent domain
        if len(parts) <= 2:
            return None
        
        # Return last two parts as parent domain
        parent = '.'.join(parts[-2:])
        
        logger.debug(f"Parent domain of '{domain}' is '{parent}'")
        return parent
        
    except Exception as e:
        logger.error(f"Error getting parent domain for '{domain}': {e}")
        return None


def get_domain_hierarchy(domain: str) -> List[str]:
    """
    Get complete domain hierarchy from most specific to least specific.
    
    Args:
        domain: Domain string (e.g., 'api.v1.support.company.com')
        
    Returns:
        List of domains in hierarchy order
        
    Examples:
        >>> get_domain_hierarchy('api.v1.support.company.com')
        ['api.v1.support.company.com', 'v1.support.company.com', 'support.company.com', 'company.com']
    """
    hierarchy = []
    
    domain = normalize_domain(domain)
    if not domain:
        return hierarchy
    
    parts = domain.split('.')
    
    # Build hierarchy from most specific to least specific
    # Stop at second-level domain (e.g., don't include just 'com')
    for i in range(len(parts) - 1):  # Changed to len(parts) - 1 to exclude TLD
        subdomain = '.'.join(parts[i:])
        hierarchy.append(subdomain)
    
    logger.debug(f"Domain hierarchy for '{domain}': {hierarchy}")
    return hierarchy


def get_domain_variants(domain: str) -> List[str]:
    """
    Get comprehensive list of domain variants for matching.
    
    Args:
        domain: Base domain string
        
    Returns:
        List of domain variants including subdomains and parent domains
        
    Examples:
        >>> get_domain_variants('support.company.com')
        ['support.company.com', 'company.com']
        >>> get_domain_variants('company.com')
        ['company.com']
    """
    variants = []
    
    domain = normalize_domain(domain)
    if not domain:
        return variants
    
    # Get complete hierarchy
    hierarchy = get_domain_hierarchy(domain)
    
    # Add all levels in hierarchy
    for variant in hierarchy:
        if variant not in variants:
            variants.append(variant)
    
    # Add www variants
    www_variants = []
    for variant in variants:
        www_variant = f"www.{variant}"
        if www_variant not in variants:
            www_variants.append(www_variant)
    
    variants.extend(www_variants)
    
    logger.debug(f"Domain variants for '{domain}': {variants}")
    return variants


def is_subdomain_of(subdomain: str, parent_domain: str) -> bool:
    """
    Check if a domain is a subdomain of another domain.
    
    Args:
        subdomain: Potential subdomain
        parent_domain: Parent domain to check against
        
    Returns:
        True if subdomain is a subdomain of parent_domain
        
    Examples:
        >>> is_subdomain_of('api.company.com', 'company.com')
        True
        >>> is_subdomain_of('company.com', 'company.com')
        False
        >>> is_subdomain_of('other.com', 'company.com')
        False
    """
    subdomain = normalize_domain(subdomain)
    parent_domain = normalize_domain(parent_domain)
    
    if not subdomain or not parent_domain:
        return False
    
    # Same domain is not a subdomain
    if subdomain == parent_domain:
        return False
    
    # Check if subdomain ends with parent domain
    if subdomain.endswith(f'.{parent_domain}'):
        logger.debug(f"'{subdomain}' is a subdomain of '{parent_domain}'")
        return True
    
    return False


def match_domain_pattern(domain: str, pattern: str) -> bool:
    """
    Match domain against a pattern (supports wildcards).
    
    Args:
        domain: Domain to match
        pattern: Pattern to match against (supports * wildcards)
        
    Returns:
        True if domain matches pattern, False otherwise
        
    Examples:
        >>> match_domain_pattern('api.company.com', '*.company.com')
        True
        >>> match_domain_pattern('company.com', '*.company.com')
        False
        >>> match_domain_pattern('support.company.com', 'support.*')
        True
    """
    domain = normalize_domain(domain)
    if not domain:
        return False
    
    # Convert pattern to regex
    pattern = pattern.lower().replace('.', r'\.')
    pattern = pattern.replace('*', r'.*')  # Changed from [^\.] to .* to match any characters including dots
    pattern = f'^{pattern}$'
    
    try:
        return bool(re.match(pattern, domain))
    except re.error:
        logger.warning(f"Invalid domain pattern: {pattern}")
        return False


def calculate_domain_similarity(domain1: str, domain2: str) -> float:
    """
    Calculate similarity score between two domains.
    
    Args:
        domain1: First domain
        domain2: Second domain
        
    Returns:
        Similarity score between 0.0 and 1.0
        
    Examples:
        >>> calculate_domain_similarity('company.com', 'company.com')
        1.0
        >>> calculate_domain_similarity('api.company.com', 'company.com')
        0.8
    """
    domain1 = normalize_domain(domain1)
    domain2 = normalize_domain(domain2)
    
    if not domain1 or not domain2:
        return 0.0
    
    # Exact match
    if domain1 == domain2:
        return 1.0
    
    # Check if one is subdomain of other
    if is_subdomain_of(domain1, domain2) or is_subdomain_of(domain2, domain1):
        return 0.8
    
    # Check common parent domain
    parts1 = domain1.split('.')
    parts2 = domain2.split('.')
    
    # Compare from right to left (TLD first)
    common_parts = 0
    for i in range(1, min(len(parts1), len(parts2)) + 1):
        if parts1[-i] == parts2[-i]:
            common_parts += 1
        else:
            break
    
    # If only TLD matches (like .com), consider it no similarity
    if common_parts <= 1:
        return 0.0
    
    # Calculate similarity based on common parts
    max_parts = max(len(parts1), len(parts2))
    similarity = common_parts / max_parts
    
    logger.debug(f"Domain similarity '{domain1}' vs '{domain2}': {similarity:.2f}")
    return similarity


def find_best_domain_match(target_domain: str, candidate_domains: List[str]) -> Tuple[Optional[str], float]:
    """
    Find best matching domain from candidates.
    
    Args:
        target_domain: Domain to match
        candidate_domains: List of candidate domains
        
    Returns:
        Tuple of (best_match, similarity_score)
    """
    target_domain = normalize_domain(target_domain)
    if not target_domain or not candidate_domains:
        return None, 0.0
    
    best_match = None
    best_score = 0.0
    
    for candidate in candidate_domains:
        candidate = normalize_domain(candidate)
        if not candidate:
            continue
        
        score = calculate_domain_similarity(target_domain, candidate)
        
        if score > best_score:
            best_score = score
            best_match = candidate
    
    logger.debug(f"Best domain match for '{target_domain}': '{best_match}' (score: {best_score:.2f})")
    return best_match, best_score


def resolve_domain_aliases(domain: str, alias_map: Dict[str, str]) -> str:
    """
    Resolve domain aliases to canonical domain.
    
    Args:
        domain: Domain to resolve
        alias_map: Dictionary mapping aliases to canonical domains
        
    Returns:
        Canonical domain or original domain if no alias found
        
    Examples:
        >>> aliases = {'old.company.com': 'company.com', 'legacy.company.com': 'company.com'}
        >>> resolve_domain_aliases('old.company.com', aliases)
        'company.com'
    """
    domain = normalize_domain(domain)
    if not domain:
        return domain
    
    # Check direct alias
    canonical = alias_map.get(domain)
    if canonical:
        logger.debug(f"Resolved alias '{domain}' -> '{canonical}'")
        return canonical
    
    # Check pattern-based aliases
    for alias_pattern, canonical_domain in alias_map.items():
        if '*' in alias_pattern and match_domain_pattern(domain, alias_pattern):
            logger.debug(f"Resolved pattern alias '{domain}' -> '{canonical_domain}' (pattern: {alias_pattern})")
            return canonical_domain
    
    return domain


class DomainMatcher:
    """
    Advanced domain matching with configurable strategies.
    """
    
    def __init__(self):
        """Initialize domain matcher."""
        self.alias_map: Dict[str, str] = {}
        self.patterns: List[str] = []
        self.similarity_threshold = 0.7
    
    def add_alias(self, alias: str, canonical: str):
        """Add domain alias mapping."""
        alias = normalize_domain(alias)
        canonical = normalize_domain(canonical)
        if alias and canonical:
            self.alias_map[alias] = canonical
            logger.debug(f"Added domain alias: {alias} -> {canonical}")
    
    def add_pattern(self, pattern: str):
        """Add domain pattern for matching."""
        if pattern and pattern not in self.patterns:
            self.patterns.append(pattern)
            logger.debug(f"Added domain pattern: {pattern}")
    
    def match_domain(self, domain: str, candidates: List[str]) -> Tuple[Optional[str], float, str]:
        """
        Match domain against candidates using multiple strategies.
        
        Args:
            domain: Domain to match
            candidates: List of candidate domains
            
        Returns:
            Tuple of (best_match, confidence, method)
        """
        domain = normalize_domain(domain)
        if not domain:
            return None, 0.0, "invalid_domain"
        
        # Strategy 1: Exact match
        if domain in candidates:
            return domain, 1.0, "exact_match"
        
        # Strategy 2: Alias resolution
        canonical = resolve_domain_aliases(domain, self.alias_map)
        if canonical != domain and canonical in candidates:
            return canonical, 0.95, "alias_resolution"
        
        # Strategy 3: Pattern matching
        for pattern in self.patterns:
            if match_domain_pattern(domain, pattern):
                # Find candidate that matches the pattern base
                pattern_base = pattern.replace('*', '').replace('.', '')
                for candidate in candidates:
                    if pattern_base in candidate:
                        return candidate, 0.9, "pattern_match"
        
        # Strategy 4: Hierarchy matching (subdomain/parent)
        hierarchy = get_domain_hierarchy(domain)
        for level in hierarchy[1:]:  # Skip first (exact) match
            if level in candidates:
                confidence = 0.8 if is_subdomain_of(domain, level) else 0.7
                return level, confidence, "hierarchy_match"
        
        # Strategy 5: Similarity matching
        best_match, similarity = find_best_domain_match(domain, candidates)
        if best_match and similarity >= self.similarity_threshold:
            return best_match, similarity, "similarity_match"
        
        return None, 0.0, "no_match" 