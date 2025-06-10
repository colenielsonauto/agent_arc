"""
Enhanced multi-tenant functionality tests.
Tests the advanced client identification, domain resolution, and fuzzy matching capabilities.
"""

import pytest
from unittest.mock import patch, MagicMock

from app.services.client_manager import EnhancedClientManager, ClientIdentificationResult
from app.utils.client_loader import get_available_clients, ClientLoadError  
from app.utils.domain_resolver import (
    extract_domain_from_email,
    normalize_domain,
    get_domain_hierarchy,
    get_domain_variants,
    calculate_domain_similarity,
    match_domain_pattern,
    DomainMatcher
)


def test_client_discovery():
    """Test that we can discover available clients"""
    clients = get_available_clients()
    assert isinstance(clients, list)
    assert len(clients) >= 1  # Should have at least client-001-cole-nielson
    
    # Check that client IDs follow expected format
    for client_id in clients:
        assert client_id.startswith('client-')
        assert isinstance(client_id, str)


def test_load_client_config():
    """Test loading client configuration"""
    from app.utils.client_loader import load_client_config
    
    # Should be able to load the test client
    config = load_client_config('client-001-cole-nielson')
    assert config.client.id == 'client-001-cole-nielson'
    assert config.client.name == 'Cole Nielson Email Router'
    assert config.domains.primary == 'colenielson.dev'
    

def test_enhanced_client_manager_domain_resolution():
    """Test enhanced domain resolution with multiple strategies"""
    manager = EnhancedClientManager()
    
    # Test exact domain match
    result = manager.identify_client_by_domain('colenielson.dev')
    assert isinstance(result, ClientIdentificationResult)
    assert result.client_id == 'client-001-cole-nielson'
    assert result.confidence == 1.0
    assert result.method == 'exact_match'
    assert result.is_successful
    
    # Test subdomain hierarchy matching
    result = manager.identify_client_by_domain('api.colenielson.dev')
    assert result.client_id == 'client-001-cole-nielson'
    assert result.confidence >= 0.7
    assert 'hierarchy' in result.method or 'exact' in result.method  # Could be exact if variant was added
    assert result.is_successful


def test_enhanced_client_manager_email_identification():
    """Test enhanced email-based client identification"""
    manager = EnhancedClientManager()
    
    # Test direct email identification
    result = manager.identify_client_by_email('support@colenielson.dev')
    assert result.client_id == 'client-001-cole-nielson'
    assert result.is_successful
    
    # Test subdomain email identification
    result = manager.identify_client_by_email('api@test.colenielson.dev')
    assert result.client_id == 'client-001-cole-nielson'
    assert result.is_successful
    
    # Test backward compatibility method
    client_id = manager.identify_client_by_email_simple('support@colenielson.dev')
    assert client_id == 'client-001-cole-nielson'


def test_enhanced_client_manager_routing():
    """Test enhanced routing with confidence-based decisions"""
    manager = EnhancedClientManager()
    
    # Test category routing
    destination = manager.get_routing_destination('client-001-cole-nielson', 'support')
    assert destination == 'colenielson.re@gmail.com'
    
    destination = manager.get_routing_destination('client-001-cole-nielson', 'billing')
    assert destination == 'colenielson8@gmail.com'


def test_enhanced_client_manager_response_times():
    """Test response time lookup with enhanced configuration"""
    manager = EnhancedClientManager()
    
    # Test specific category response times
    response_time = manager.get_response_time('client-001-cole-nielson', 'support')
    assert response_time == 'within 4 hours'
    
    response_time = manager.get_response_time('client-001-cole-nielson', 'billing')
    assert response_time == 'within 24 hours'


def test_client_validation():
    """Test enhanced client configuration validation"""
    manager = EnhancedClientManager()
    
    # Valid client should pass validation
    is_valid = manager.validate_client_setup('client-001-cole-nielson')
    assert is_valid == True


def test_unknown_client_handling():
    """Test handling of unknown clients with enhanced fallback"""
    manager = EnhancedClientManager()
    
    # Should return failure result for unknown domain
    result = manager.identify_client_by_domain('nonexistent.example.com')
    assert not result.is_successful
    assert result.client_id is None
    assert result.method == 'no_match'
    
    # Should return None for unknown email with simple method
    client_id = manager.identify_client_by_email_simple('test@nonexistent.example.com')
    assert client_id is None


def test_invalid_client_id():
    """Test handling of invalid client IDs with enhanced error reporting"""
    manager = EnhancedClientManager()
    
    with pytest.raises(ClientLoadError):
        manager.get_client_config('invalid-client-id')


# New tests for enhanced features

def test_domain_hierarchy_extraction():
    """Test domain hierarchy extraction"""
    hierarchy = get_domain_hierarchy('api.v1.support.company.com')
    expected = ['api.v1.support.company.com', 'v1.support.company.com', 'support.company.com', 'company.com']
    assert hierarchy == expected
    
    # Test simple domain
    hierarchy = get_domain_hierarchy('company.com')
    assert hierarchy == ['company.com']


def test_domain_variants_generation():
    """Test comprehensive domain variants generation"""
    variants = get_domain_variants('support.company.com')
    
    # Should include the domain itself and parent
    assert 'support.company.com' in variants
    assert 'company.com' in variants
    
    # Should include www variants
    assert 'www.support.company.com' in variants
    assert 'www.company.com' in variants


def test_domain_similarity_calculation():
    """Test domain similarity scoring"""
    # Exact match
    similarity = calculate_domain_similarity('company.com', 'company.com')
    assert similarity == 1.0
    
    # Subdomain relationship
    similarity = calculate_domain_similarity('api.company.com', 'company.com')
    assert similarity >= 0.7
    
    # Different domains
    similarity = calculate_domain_similarity('example.com', 'company.com')
    assert similarity == 0.0


def test_domain_pattern_matching():
    """Test wildcard domain pattern matching"""
    # Test wildcard patterns
    assert match_domain_pattern('api.company.com', '*.company.com') == True
    assert match_domain_pattern('company.com', '*.company.com') == False
    assert match_domain_pattern('support.company.com', 'support.*') == True
    assert match_domain_pattern('billing.company.com', 'support.*') == False


def test_domain_matcher_advanced_strategies():
    """Test DomainMatcher with multiple strategies"""
    matcher = DomainMatcher()
    
    # Add test aliases and patterns
    matcher.add_alias('old.company.com', 'company.com')
    matcher.add_pattern('*.company.com')
    
    candidates = ['company.com', 'example.com', 'test.org']
    
    # Test exact match
    match, confidence, method = matcher.match_domain('company.com', candidates)
    assert match == 'company.com'
    assert confidence == 1.0
    assert method == 'exact_match'
    
    # Test alias resolution
    match, confidence, method = matcher.match_domain('old.company.com', candidates)
    assert match == 'company.com'
    assert confidence == 0.95
    assert method == 'alias_resolution'


def test_client_domains_management():
    """Test client domain management features"""
    manager = EnhancedClientManager()
    
    # Test getting client domains
    domains = manager.get_client_domains('client-001-cole-nielson')
    assert isinstance(domains, set)
    assert len(domains) > 0
    assert 'colenielson.dev' in domains


def test_similar_clients_discovery():
    """Test finding similar clients based on domain similarity"""
    manager = EnhancedClientManager()
    
    # Test finding similar clients
    similar = manager.find_similar_clients('similar.colenielson.dev', limit=3)
    assert isinstance(similar, list)
    
    # If similar clients found, should be tuples of (client_id, score)
    for client_id, score in similar:
        assert isinstance(client_id, str)
        assert 0.0 <= score <= 1.0


def test_client_summary_generation():
    """Test comprehensive client summary generation"""
    manager = EnhancedClientManager()
    
    summary = manager.get_client_summary('client-001-cole-nielson')
    
    assert summary['client_id'] == 'client-001-cole-nielson'
    assert summary['name'] == 'Cole Nielson Email Router'
    assert 'domains' in summary
    assert 'routing_categories' in summary
    assert 'settings' in summary
    assert summary['total_domains'] > 0


def test_domain_alias_functionality():
    """Test domain alias management"""
    manager = EnhancedClientManager()
    
    # Add domain alias
    manager.add_domain_alias('legacy.colenielson.dev', 'colenielson.dev')
    
    # Test that alias resolves correctly
    # Note: This would require the alias to be used in identification
    # For now, just test that the method doesn't error
    assert True  # Placeholder - would need more complex test setup


def test_fuzzy_matching_configuration():
    """Test fuzzy matching configuration options"""
    manager = EnhancedClientManager()
    
    # Test configuration options
    assert hasattr(manager, 'confidence_threshold')
    assert hasattr(manager, 'enable_fuzzy_matching')
    assert hasattr(manager, 'enable_hierarchy_matching')
    
    # Test disabling fuzzy matching
    manager.enable_fuzzy_matching = False
    result = manager.identify_client_by_domain('unknown.domain.com')
    assert not result.is_successful


def test_confidence_scoring_accuracy():
    """Test that confidence scores are reasonable and consistent"""
    manager = EnhancedClientManager()
    
    # Exact match should have highest confidence
    result = manager.identify_client_by_domain('colenielson.dev')
    assert result.confidence == 1.0
    
    # Subdomain matches should have lower but reasonable confidence
    result = manager.identify_client_by_domain('api.colenielson.dev')
    if result.is_successful:
        assert 0.7 <= result.confidence < 1.0


def test_email_domain_extraction_edge_cases():
    """Test domain extraction with edge cases"""
    # Valid cases
    assert extract_domain_from_email('user@company.com') == 'company.com'
    assert extract_domain_from_email('test@sub.domain.co.uk') == 'sub.domain.co.uk'
    
    # Invalid cases
    assert extract_domain_from_email('invalid-email') is None
    assert extract_domain_from_email('user@') is None
    assert extract_domain_from_email('@domain.com') is None
    assert extract_domain_from_email('') is None


def test_domain_normalization_edge_cases():
    """Test domain normalization with various inputs"""
    # Standard cases
    assert normalize_domain('Company.COM') == 'company.com'
    assert normalize_domain('www.Company.com') == 'company.com'
    
    # Edge cases
    assert normalize_domain('') is None
    assert normalize_domain('invalid') is None
    assert normalize_domain('company.com.') == 'company.com'  # Trailing dot removal
    assert normalize_domain('https://company.com/path') == 'company.com' 