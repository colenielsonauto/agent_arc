# Security Infrastructure

This directory contains security-related infrastructure components for the email router system.

## Overview

Security is paramount in email processing. This module provides:
- **Encryption**: End-to-end encryption for sensitive data
- **Key Management**: Secure storage and rotation of API keys
- **Authentication**: OAuth2, JWT, and API key management
- **Authorization**: Role-based access control (RBAC)
- **Audit Logging**: Comprehensive security event tracking
- **Data Privacy**: GDPR/CCPA compliance tools

## Planned Components

### Key Management (`key_manager.py`)
```python
class KeyManager:
    """Secure key storage and rotation."""
    
    async def get_key(self, key_name: str) -> str:
        """Retrieve decrypted key from secure storage."""
        
    async def rotate_key(self, key_name: str) -> None:
        """Rotate API keys and update dependencies."""
        
    async def encrypt_data(self, data: str, key_name: str) -> str:
        """Encrypt sensitive data."""
```

### Authentication (`auth.py`)
```python
class AuthenticationManager:
    """Handle various authentication methods."""
    
    async def verify_oauth_token(self, token: str) -> User:
        """Verify OAuth2 tokens."""
        
    async def verify_api_key(self, api_key: str) -> Client:
        """Verify API keys."""
        
    async def generate_jwt(self, user: User) -> str:
        """Generate JWT tokens."""
```

### Encryption (`encryption.py`)
```python
class EncryptionService:
    """End-to-end encryption for emails."""
    
    async def encrypt_email(self, email: Email) -> EncryptedEmail:
        """Encrypt email content and attachments."""
        
    async def decrypt_email(self, encrypted: EncryptedEmail) -> Email:
        """Decrypt email for authorized access."""
```

### Privacy (`privacy.py`)
```python
class PrivacyManager:
    """GDPR/CCPA compliance tools."""
    
    async def anonymize_email(self, email: Email) -> Email:
        """Remove PII from emails."""
        
    async def export_user_data(self, user_id: str) -> UserDataExport:
        """Export all user data for GDPR requests."""
        
    async def delete_user_data(self, user_id: str) -> None:
        """Complete user data deletion."""
```

### Audit (`audit.py`)
```python
class AuditLogger:
    """Security event logging."""
    
    async def log_access(self, user: User, resource: str, action: str):
        """Log resource access."""
        
    async def log_security_event(self, event: SecurityEvent):
        """Log security-relevant events."""
```

## Security Best Practices

### 1. Zero-Trust Architecture
- Never trust, always verify
- Assume breach mentality
- Least privilege access

### 2. Encryption Standards
- AES-256 for data at rest
- TLS 1.3 for data in transit
- End-to-end encryption for sensitive emails

### 3. Key Management
- Use HashiCorp Vault or cloud KMS
- Regular key rotation (90 days)
- Separate keys for different environments

### 4. Authentication
- Multi-factor authentication (MFA)
- OAuth2 with PKCE for web clients
- Short-lived tokens (15 minutes)

### 5. Data Privacy
- Minimal data collection
- Automatic PII detection
- Data retention policies

## Integration Examples

### Secure Email Processing
```python
from infrastructure.security import SecurityManager

security = SecurityManager()

# Decrypt API keys
email_api_key = await security.get_key("gmail_api_key")
llm_api_key = await security.get_key("openai_api_key")

# Process email with audit trail
async with security.audit_context(user_id, "email_processing"):
    # Decrypt email if needed
    if email.is_encrypted:
        email = await security.decrypt_email(email)
    
    # Process with security context
    result = await process_email(email)
    
    # Log sensitive operations
    await security.log_access(user_id, email.id, "processed")
```

### GDPR Compliance
```python
# Handle data export request
export = await privacy_manager.export_user_data(user_id)
await send_data_export(user_email, export)

# Handle deletion request
await privacy_manager.delete_user_data(user_id)
await memory_store.clear_user_data(user_id)
await audit_logger.log_gdpr_deletion(user_id)
```

## Security Checklist

- [ ] All API keys stored in secure vault
- [ ] Email content encrypted at rest
- [ ] TLS enforced for all connections
- [ ] Authentication required for all endpoints
- [ ] Audit logging enabled
- [ ] PII detection and masking active
- [ ] Regular security scans
- [ ] Incident response plan in place
- [ ] Data retention policies configured
- [ ] GDPR/CCPA compliance verified

## Tools and Services

### Recommended Tools
- **HashiCorp Vault**: Secret management
- **AWS KMS / GCP KMS**: Cloud key management
- **OAuth2 Proxy**: Authentication gateway
- **Open Policy Agent**: Fine-grained authorization
- **Falco**: Runtime security monitoring

### Security Scanning
- **Snyk**: Dependency vulnerability scanning
- **Trivy**: Container security scanning
- **OWASP ZAP**: Web application security testing
- **GitLeaks**: Secret scanning in code 