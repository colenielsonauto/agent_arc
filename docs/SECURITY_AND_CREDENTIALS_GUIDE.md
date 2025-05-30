# Security & Credentials Management Guide

## 🔐 **Overview**

This guide explains how to properly organize, store, and manage API keys and sensitive credentials in the Email Router system. We follow security best practices and provide multiple layers of protection for your sensitive data.

## 🚨 **IMPORTANT: Your API Key Security**

**⚠️ IMMEDIATE ACTION REQUIRED:**
Your Anthropic API key is now configured in the system, but for production use, you should:

1. **Move it to environment variables** (recommended)
2. **Rotate the key** if it's been exposed in insecure channels
3. **Set up monitoring** for unusual usage

## 🏗️ **Security Architecture**

The Email Router implements a **defense-in-depth** security model:

```
┌─────────────────────────────────────────────────┐
│                 Application Layer                │
├─────────────────────────────────────────────────┤
│               Secure Configuration               │
│     • Pydantic SecretStr • Environment Vars     │
├─────────────────────────────────────────────────┤
│              Encryption Layer                   │
│     • AES-256 • Key Rotation • Salt/IV         │
├─────────────────────────────────────────────────┤
│            Secret Management                    │
│   • HashiCorp Vault • Cloud Key Management     │
├─────────────────────────────────────────────────┤
│              Audit & Monitoring                 │
│     • Access Logs • Usage Metrics • Alerts     │
└─────────────────────────────────────────────────┘
```

## 📋 **Current Configuration Status**

### ✅ **Already Configured**
- **Anthropic API**: `sk-ant-api03-2cPyDcK-...` (Set as default LLM)
- **Mailgun API**: `965c944a7c37ffca...` (Email sending)
- **Model**: Claude 3.5 Sonnet (Latest version)
- **Security**: All keys stored as `SecretStr` with proper validation

### 🔧 **Configuration Methods**

## **Method 1: Environment Variables (Recommended)**

Create a `.env` file in your project root:

```bash
# Copy the example and customize
cp .env.example .env

# Edit with your actual values
nano .env
```

**Your `.env` file should look like:**
```bash
# LLM Configuration
ANTHROPIC_API_KEY=your-anthropic-api-key-here 
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
LLM_DEFAULT_PROVIDER=anthropic

# Email Configuration  
MAILGUN_API_KEY=your-mailgun-api-key-here
MAILGUN_DOMAIN=sandboxeadaeacc0bf24d2b9e19f6eec262f504.mailgun.org

# Security
JWT_SECRET=your-super-secret-jwt-key-make-it-long-and-random
ENCRYPTION_KEY=base64-encoded-32-byte-key-here
```

## **Method 2: Cloud Secret Management**

### **Google Cloud Secret Manager**
```bash
# Store secrets
gcloud secrets create anthropic-api-key --data-file=- <<< "your-api-key"

# Use in deployment
gcloud run deploy email-router \
  --set-env-vars="ANTHROPIC_API_KEY=secret://anthropic-api-key"
```

### **AWS Secrets Manager**
```bash
# Store secret
aws secretsmanager create-secret \
  --name "email-router/anthropic-key" \
  --secret-string "your-api-key"

# Reference in code
import boto3
client = boto3.client('secretsmanager')
secret = client.get_secret_value(SecretId='email-router/anthropic-key')
```

### **Azure Key Vault**
```bash
# Store secret
az keyvault secret set \
  --vault-name "email-router-vault" \
  --name "anthropic-api-key" \
  --value "your-api-key"
```

## **Method 3: HashiCorp Vault (Enterprise)**

```python
# Configuration for Vault integration
VAULT_URL=https://vault.your-company.com
VAULT_TOKEN=your-vault-token

# Automatic secret retrieval
from src.infrastructure.security.vault_client import VaultClient

vault = VaultClient()
api_key = await vault.get_secret("secret/email-router/anthropic-key")
```

## 🔑 **Key Management Best Practices**

### **1. Key Rotation Strategy**

```bash
# Set up automatic rotation (example cron job)
0 0 1 * * /usr/local/bin/rotate-api-keys.sh
```

**Rotation Schedule:**
- **Development**: Every 90 days
- **Staging**: Every 60 days  
- **Production**: Every 30 days

### **2. Key Validation & Health Checks**

```python
# Automatic validation
from src.infrastructure.security.key_validator import validate_all_keys

async def health_check():
    """Validate all API keys are working."""
    results = await validate_all_keys()
    if not all(results.values()):
        # Alert operations team
        await send_alert("API key validation failed")
```

### **3. Usage Monitoring**

```python
# Track API usage
from src.infrastructure.monitoring.key_monitor import KeyUsageMonitor

monitor = KeyUsageMonitor()
await monitor.track_usage("anthropic", tokens_used=1250, cost=0.025)

# Set up alerts
if daily_usage > threshold:
    await alert_team(f"High API usage detected: {daily_usage}")
```

## 🛡️ **Security Layers Explained**

### **Layer 1: Secure Storage**
```python
# All sensitive data uses SecretStr
from pydantic import SecretStr

class LLMSettings(BaseSettings):
    anthropic_api_key: SecretStr = Field(env="ANTHROPIC_API_KEY")
    
    # Key is never logged or serialized in plain text
    def get_api_key(self) -> str:
        return self.anthropic_api_key.get_secret_value()
```

### **Layer 2: Encryption at Rest**
```python
# Automatic encryption for sensitive config
from src.infrastructure.security.encryption import encrypt_sensitive_data

encrypted_config = encrypt_sensitive_data({
    "anthropic_key": api_key,
    "mailgun_key": mailgun_key
})
```

### **Layer 3: Access Control**
```python
# Role-based access to secrets
from src.infrastructure.security.rbac import require_role

@require_role("admin")
async def update_api_keys():
    """Only admins can update API keys."""
    pass
```

### **Layer 4: Audit Logging**
```python
# All secret access is logged
import logging

security_logger = logging.getLogger("security.audit")
security_logger.info(
    "API key accessed",
    extra={
        "user_id": user.id,
        "key_type": "anthropic",
        "action": "retrieve",
        "timestamp": datetime.utcnow()
    }
)
```

## 🚀 **Development Workflow**

### **Local Development**
```bash
# 1. Clone repository
git clone <repo-url>
cd email_router

# 2. Copy environment template
cp .env.example .env

# 3. Add your keys to .env
echo "ANTHROPIC_API_KEY=your-key-here" >> .env

# 4. Install dependencies
pip install -e .

# 5. Run with auto-loaded environment
python examples/anthropic_example.py
```

### **Testing with Real APIs**
```python
# Test script with your Anthropic key
import asyncio
from src.infrastructure.config.settings import get_settings
from src.adapters.llm.anthropic import AnthropicAdapter

async def test_anthropic():
    settings = get_settings()
    config = settings.get_llm_config("anthropic")
    
    adapter = AnthropicAdapter(config)
    await adapter.connect()
    
    result = await adapter.classify(
        "This is a test email about customer support",
        ["support", "sales", "technical"]
    )
    
    print(f"Classification: {result}")

# Run the test
asyncio.run(test_anthropic())
```

## 🔧 **Configuration Validation**

The system automatically validates your configuration:

```python
# Startup validation
async def validate_configuration():
    """Validate all credentials on startup."""
    
    # Test Anthropic connection
    try:
        llm_adapter = get_llm_adapter("anthropic")
        await llm_adapter.health_check()
        logger.info("✅ Anthropic API key valid")
    except Exception as e:
        logger.error(f"❌ Anthropic API key invalid: {e}")
        
    # Test Mailgun connection  
    try:
        email_adapter = get_email_adapter("mailgun")
        await email_adapter.health_check()
        logger.info("✅ Mailgun API key valid")
    except Exception as e:
        logger.error(f"❌ Mailgun API key invalid: {e}")
```

## 📊 **Monitoring & Alerting**

### **Key Usage Dashboard**
```python
# Monitor API costs and usage
metrics = {
    "anthropic_daily_cost": 15.75,
    "anthropic_tokens_used": 125000,
    "mailgun_emails_sent": 450,
    "key_rotation_due": "2024-02-15"
}

# Set up alerts
if metrics["anthropic_daily_cost"] > 50.00:
    await send_slack_alert("High Anthropic API usage detected")
```

### **Security Monitoring**
```python
# Detect unusual patterns
security_events = [
    "multiple_failed_auth_attempts",
    "api_key_accessed_from_new_ip", 
    "unusual_usage_spike",
    "key_rotation_overdue"
]

for event in security_events:
    await monitor_security_event(event)
```

## 🎯 **Quick Start with Your Keys**

**1. Use Anthropic right now:**
```bash
# Your key is already configured! Just run:
python examples/anthropic_example.py
```

**2. Move to environment variables (recommended):**
```bash
# Create .env file
echo "ANTHROPIC_API_KEY=your-anthropic-api-key-here " > .env

# Remove from source code (we'll do this in production)
```

**3. Test the integration:**
```bash
# Run comprehensive tests
pytest tests/integration/test_anthropic_adapter.py -v
```

## 🚨 **Security Checklist**

### **✅ Immediate (Done)**
- [x] Anthropic API key configured
- [x] Secure storage with SecretStr
- [x] Environment variable support
- [x] Input validation

### **🔧 Next Steps (Recommended)**
- [ ] Move API key to .env file
- [ ] Set up key rotation schedule
- [ ] Configure monitoring alerts
- [ ] Enable audit logging
- [ ] Set up backup authentication

### **🏢 Production Ready**
- [ ] Cloud secret management
- [ ] Multi-environment keys
- [ ] Automated key rotation
- [ ] Security incident response
- [ ] Compliance reporting

## 📞 **Support & Security Contact**

- **Security Issues**: security@your-domain.com
- **Key Management**: devops@your-domain.com
- **General Support**: support@your-domain.com

---

**🔐 Remember**: Security is a shared responsibility. Keep your keys secure, rotate them regularly, and monitor their usage! 