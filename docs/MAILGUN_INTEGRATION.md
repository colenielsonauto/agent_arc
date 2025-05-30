# Mailgun Integration Guide

## Overview

This document explains how the Mailgun email service has been integrated into the Email Router system. The integration follows the project's hexagonal architecture principles and provides a clean, consistent interface for sending emails through Mailgun.

## Architecture Integration

The Mailgun integration consists of several components that fit into the existing architecture:

### 1. Core Interface Implementation
- **Location**: `src/adapters/email/mailgun.py`
- **Class**: `MailgunAdapter`
- **Implements**: `EmailProviderInterface`

### 2. Configuration Integration
- **Location**: `src/infrastructure/config/settings.py`
- **Settings**: `EmailSettings` class includes Mailgun credentials
- **Environment**: Supports environment variable overrides

### 3. Adapter Registry
- **Location**: `src/adapters/__init__.py`
- **Registration**: `"mailgun": "adapters.email.mailgun.MailgunAdapter"`

## Configuration

### Default Credentials
The system is pre-configured with your provided Mailgun credentials:

```python
# From src/infrastructure/config/settings.py
mailgun_api_key: SecretStr = "your-mailgun-api-key-here"
mailgun_domain: str = "sandboxeadaeacc0bf24d2b9e19f6eec262f504.mailgun.org"
mailgun_base_url: str = "https://api.mailgun.net"
```

### Environment Variables
You can override these settings using environment variables:

```bash
export MAILGUN_API_KEY="your-api-key-here"
export MAILGUN_DOMAIN="your-domain.mailgun.org"
export MAILGUN_BASE_URL="https://api.mailgun.net"
```

## Usage Examples

### Basic Email Sending

```python
from src.core.interfaces.email_provider import (
    EmailProviderConfig, EmailProvider, EmailAddress
)
from src.adapters.email.mailgun import MailgunAdapter
from src.infrastructure.config.settings import get_settings

# Get configuration
settings = get_settings()
config = EmailProviderConfig(
    provider=EmailProvider.MAILGUN,
    credentials=settings.get_email_config("mailgun")["credentials"]
)

# Create adapter
adapter = MailgunAdapter(config)

# Send email
async def send_email():
    await adapter.connect()
    
    message_id = await adapter.send_email(
        to=[EmailAddress(email="recipient@example.com", name="Recipient")],
        subject="Hello from Mailgun!",
        body_text="This email was sent via the Email Router's Mailgun adapter."
    )
    
    await adapter.disconnect()
    return message_id
```

### Advanced Features

#### HTML Email with Attachments
```python
async def send_rich_email():
    await adapter.connect()
    
    # Create attachment
    attachment = EmailAttachment(
        filename="document.pdf",
        content_type="application/pdf",
        size=len(pdf_data),
        data=pdf_data
    )
    
    message_id = await adapter.send_email(
        to=[EmailAddress(email="user@example.com")],
        subject="Rich Email Example",
        body_text="Plain text version",
        body_html="<h1>HTML Version</h1><p>Rich content here!</p>",
        cc=[EmailAddress(email="cc@example.com")],
        attachments=[attachment],
        headers={"X-Custom-Header": "Custom Value"}
    )
    
    await adapter.disconnect()
```

#### Email Validation
```python
async def validate_email_address(email: str):
    await adapter.connect()
    
    result = await adapter.validate_email(email)
    print(f"Validation result: {result}")
    
    await adapter.disconnect()
```

#### Webhook Setup
```python
async def setup_webhooks():
    config = EmailProviderConfig(
        provider=EmailProvider.MAILGUN,
        credentials=settings.get_email_config("mailgun")["credentials"],
        webhook_url="https://your-app.com/webhooks/mailgun"
    )
    
    adapter = MailgunAdapter(config)
    await adapter.connect()
    
    webhook_id = await adapter.setup_webhook([
        "delivered", "opened", "clicked", "bounced"
    ])
    
    await adapter.disconnect()
```

## API Methods

The `MailgunAdapter` implements all methods from `EmailProviderInterface`:

### Core Methods
- ✅ `connect()` - Establishes connection to Mailgun API
- ✅ `disconnect()` - Closes connection
- ✅ `send_email()` - Sends emails with full feature support
- ✅ `setup_webhook()` - Configures event webhooks
- ✅ `get_domain_info()` - Retrieves domain information
- ✅ `get_stats()` - Gets email statistics
- ✅ `validate_email()` - Validates email addresses

### Limitations
Some methods are not applicable to Mailgun's architecture:
- ⚠️ `fetch_emails()` - Returns empty list (Mailgun is send-only by default)
- ⚠️ `fetch_email_by_id()` - Not implemented (no email storage)
- ⚠️ `mark_as_read/unread()` - Not applicable
- ⚠️ `add_labels/remove_labels()` - Not applicable
- ⚠️ `delete_emails()` - Not applicable
- ⚠️ `create_draft()` - Returns placeholder ID

These limitations are by design since Mailgun is primarily a transactional email service, not an email storage provider.

## Testing

### Unit Tests
Run the comprehensive test suite:

```bash
# Run all Mailgun tests
pytest tests/integration/test_mailgun_adapter.py -v

# Run specific test
pytest tests/integration/test_mailgun_adapter.py::TestMailgunAdapter::test_send_email -v
```

### Integration Testing
The test file includes both mocked tests and a real API test (commented out):

```python
# Uncomment in tests/integration/test_mailgun_adapter.py
async def test_real_mailgun_send():
    # WARNING: This sends a real email!
    pass
```

### Example Script
Run the comprehensive example:

```bash
python examples/mailgun_send_example.py
```

## Error Handling

The adapter includes comprehensive error handling:

```python
try:
    await adapter.send_email(...)
except RuntimeError as e:
    # Handle connection or API errors
    print(f"API Error: {e}")
except ValueError as e:
    # Handle configuration errors
    print(f"Config Error: {e}")
```

## Monitoring and Logging

The adapter provides detailed logging:

```python
import logging

# Enable debug logging
logging.getLogger("src.adapters.email.mailgun").setLevel(logging.DEBUG)
```

Log messages include:
- ✅ Connection status
- ✅ Email sending results
- ✅ Webhook setup status
- ⚠️ Warnings for unsupported operations
- ❌ Detailed error information

## Security Considerations

### API Key Management
- API keys are stored as `SecretStr` in configuration
- Environment variables are preferred for production
- Consider using HashiCorp Vault for enterprise deployments

### Webhook Security
- Use HTTPS endpoints for webhooks
- Implement signature verification for webhook payloads
- Validate webhook source IPs

## Comparison with Original Code

Your original function:
```python
def send_simple_message():
    return requests.post(
        "https://api.mailgun.net/v3/sandboxeadaeacc0bf24d2b9e19f6eec262f504.mailgun.org/messages",
        auth=("api", os.getenv('API_KEY', 'API_KEY')),
        data={"from": "Mailgun Sandbox <postmaster@sandboxeadaeacc0bf24d2b9e19f6eec262f504.mailgun.org>",
            "to": "Cole Nielson <colenielson6@gmail.com>",
            "subject": "Hello Cole Nielson",
            "text": "Congratulations Cole Nielson, you just sent an email with Mailgun! You are truly awesome!"})
```

Equivalent using the new adapter:
```python
async def send_simple_message():
    settings = get_settings()
    config = EmailProviderConfig(
        provider=EmailProvider.MAILGUN,
        credentials=settings.get_email_config("mailgun")["credentials"]
    )
    
    adapter = MailgunAdapter(config)
    await adapter.connect()
    
    message_id = await adapter.send_email(
        to=[EmailAddress(email="colenielson6@gmail.com", name="Cole Nielson")],
        subject="Hello Cole Nielson",
        body_text="Congratulations Cole Nielson, you just sent an email with Mailgun! You are truly awesome!"
    )
    
    await adapter.disconnect()
    return message_id
```

## Benefits of the Integration

1. **Consistent Interface**: Same API for all email providers (Gmail, Mailgun, etc.)
2. **Type Safety**: Full type hints and validation with Pydantic
3. **Async Support**: Built for high-performance async operations
4. **Error Handling**: Comprehensive error handling and logging
5. **Testing**: Extensive test coverage with mocking support
6. **Configuration**: Flexible configuration with environment variable support
7. **Extensibility**: Easy to add new features and providers
8. **Security**: Secure credential management
9. **Monitoring**: Built-in logging and metrics support

## Future Enhancements

Potential improvements for the Mailgun integration:

1. **Incoming Email Support**: Implement webhook handlers for receiving emails
2. **Template Support**: Add support for Mailgun templates
3. **Bulk Operations**: Batch email sending optimization
4. **Advanced Analytics**: Enhanced tracking and analytics
5. **A/B Testing**: Support for email A/B testing
6. **Compliance**: GDPR and other compliance features

## Support

For issues with the Mailgun integration:

1. Check the logs for detailed error messages
2. Verify your API credentials are correct
3. Ensure your domain is properly configured in Mailgun
4. Review the test suite for usage examples
5. Check Mailgun's API documentation for service status

The integration is designed to be robust and provide clear error messages to help with troubleshooting. 