# 🛠️ Email Router - Development Guide

## Quick Start

### Prerequisites
- Python 3.9+
- Anthropic API key
- Mailgun account (for email sending)
- Code editor with Python support

### Environment Setup
```bash
# Clone and navigate to project
git clone https://github.com/colenielsonauto/email_router.git
cd email_router

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install fastapi uvicorn httpx python-dotenv

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### Required Environment Variables
```bash
# Core AI
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# Email sending
MAILGUN_API_KEY=your-mailgun-key-here
MAILGUN_DOMAIN=your-domain.mailgun.org

# Application
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
```

## Development Workflow

### 1. Daily Development Cycle
```bash
# Activate environment
source .venv/bin/activate

# Start the API server
cd src/api && python main.py
# Server runs at http://localhost:8000

# In another terminal, run tests
python scripts/test_ai_integration.py
python scripts/test_mailgun_simple.py

# View API documentation
open http://localhost:8000/docs
```

### 2. Making Changes
1. **Edit code** in `src/` directory
2. **Test changes** using scripts in `scripts/`
3. **Check API** at http://localhost:8000/docs
4. **Verify health** at http://localhost:8000/health

### 3. Code Quality
```bash
# Format code (if black is installed)
black src/

# Type checking (if mypy is installed)
mypy src/

# Manual code review checklist:
# - Type hints on all functions
# - Proper error handling
# - Async/await for I/O operations
# - Meaningful variable names
```

## Development Scripts

### 🧪 Core Testing Scripts

#### `scripts/test_ai_integration.py`
**Purpose**: Comprehensive test of AI integration and API functionality

```bash
python scripts/test_ai_integration.py
```

**What it tests**:
- ✅ Direct AI classifier functionality
- ✅ FastAPI endpoint integration
- ✅ Health check endpoints
- ✅ Real AI classification with Claude

**Expected output**:
```
🚀 Email Router AI Integration Tests
==================================================
🧪 Testing AI Classifier Directly
✅ Direct AI Test Successful!
   Category: support
   Confidence: 0.98

🌐 Testing AI via FastAPI Endpoint  
✅ API Test Successful!
   Processing time: 2814.066ms

🏥 Testing Health Endpoints
✅ Basic Health: healthy
✅ Detailed Health: healthy

🎯 3/3 tests passed
```

#### `scripts/test_mailgun_simple.py`
**Purpose**: Test Mailgun email sending functionality

```bash
python scripts/test_mailgun_simple.py
```

**What it tests**:
- ✅ Mailgun API connection
- ✅ Email sending capability
- ✅ Email address validation
- ✅ Domain configuration

#### `scripts/test_mailgun_authorized.py`
**Purpose**: Manage authorized recipients for sandbox domain

```bash
python scripts/test_mailgun_authorized.py
```

**Use case**: Add email addresses to Mailgun sandbox domain for testing

### 🔧 Legacy Scripts (Reference Only)

These scripts exist for the previous architecture but contain useful patterns:

- `scripts/test_gmail_auth.py` - Gmail OAuth2 authentication
- `scripts/watch_gmail.py` - Gmail watch registration
- `scripts/smoke_test.py` - System health testing

## API Development

### Starting the Server
```bash
# Development server with auto-reload
cd src/api && python main.py

# Production-style server
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

### Testing API Endpoints

#### Health Checks
```bash
# Basic health
curl http://localhost:8000/health

# Detailed component status
curl http://localhost:8000/health/detailed

# System status
curl http://localhost:8000/status
```

#### Email Classification
```bash
# Test classification endpoint
curl -X POST "http://localhost:8000/classify" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Help with billing issue",
    "body": "I have a question about my latest invoice.",
    "sender": "customer@example.com"
  }'
```

### API Documentation
- **Interactive docs**: http://localhost:8000/docs
- **ReDoc format**: http://localhost:8000/redoc
- **OpenAPI schema**: http://localhost:8000/openapi.json

## Adding New Features

### 1. Adding API Endpoints

```python
# In src/api/main.py
@app.post("/new-endpoint")
async def new_endpoint(request: NewRequest) -> NewResponse:
    """New endpoint description."""
    try:
        # Implementation
        return NewResponse(...)
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Error message")
```

### 2. Adding AI Capabilities

```python
# In src/core/ai/ai_classifier.py
async def new_ai_function(self, text: str) -> Dict[str, Any]:
    """New AI-powered function."""
    prompt = f"Analyze this text: {text}"
    
    response = await self.client.post(...)
    return self.parse_response(response)
```

### 3. Adding Email Integrations

```python
# In src/adapters/email/
class NewEmailAdapter(EmailProviderInterface):
    async def send_email(self, ...):
        """Implement email sending for new provider."""
        pass
```

## Testing Strategy

### 1. Quick Testing (Development)
```bash
# Run all integration tests
python scripts/test_ai_integration.py

# Test specific component
python scripts/test_mailgun_simple.py
```

### 2. Manual Testing
```bash
# Start server
cd src/api && python main.py

# Test in browser
open http://localhost:8000/docs

# Test classification
# Use the interactive docs to send test emails
```

### 3. API Testing with curl
```bash
# Health check
curl -s http://localhost:8000/health | python3 -m json.tool

# Classification test
curl -X POST "http://localhost:8000/classify" \
  -H "Content-Type: application/json" \
  -d '{"subject": "Test", "body": "Test email"}' | python3 -m json.tool
```

## Debugging

### 1. Common Issues

**Import Errors**:
```bash
# Solution: Check Python path
python -c "import sys; print(sys.path)"
# Ensure you're running from project root
```

**AI Classification Fails**:
```bash
# Check API key
python -c "import os; print('ANTHROPIC_API_KEY' in os.environ)"
# Check internet connection
curl -s https://api.anthropic.com
```

**Mailgun Sending Fails**:
```bash
# Check domain configuration
python scripts/test_mailgun_simple.py
# Add authorized recipients for sandbox domains
```

### 2. Logging

```python
# Enable debug logging
import logging
logging.getLogger("src.core.ai").setLevel(logging.DEBUG)
logging.getLogger("src.adapters.email").setLevel(logging.DEBUG)
```

### 3. Health Monitoring

```bash
# Check all component health
curl http://localhost:8000/health/detailed | python3 -m json.tool
```

## Code Organization

### 1. File Structure Rules
- **Core logic**: `src/core/` - Business logic, AI processing
- **API endpoints**: `src/api/` - FastAPI routes and handlers
- **External services**: `src/adapters/` - Email, AI, storage adapters
- **Development tools**: `scripts/` - Testing and utility scripts
- **Documentation**: `docs/` - Architecture and development guides

### 2. Import Patterns
```python
# Standard library
import asyncio
import os
from typing import Dict, Any

# Third-party
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Local imports
from core.ai import AIEmailClassifier
from adapters.email.mailgun import MailgunAdapter
```

### 3. Async Patterns
```python
# All I/O operations should be async
async def process_email(email_data):
    # AI classification
    classification = await ai_classifier.classify_email(...)
    
    # Email sending
    result = await email_adapter.send_email(...)
    
    return result
```

## Environment Management

### 1. Environment Variables
```bash
# Required for basic functionality
ANTHROPIC_API_KEY=sk-ant-api03-...
MAILGUN_API_KEY=your-key...
MAILGUN_DOMAIN=your-domain...

# Optional for enhanced features
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
```

### 2. Different Environments
```bash
# Development
ENVIRONMENT=development
DEBUG=true

# Production  
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING
```

## Performance Tips

### 1. Local Development
- Use `--reload` flag for auto-restart during development
- Enable debug logging for troubleshooting
- Test with small email samples first

### 2. API Optimization
- Use async/await for all I/O operations
- Implement proper error handling
- Monitor response times via health checks

### 3. AI Performance
- Cache classification results when appropriate
- Use appropriate model temperature settings
- Monitor API usage and costs

## Next Steps

### 1. After Basic Setup
1. Get AI classification working
2. Verify Mailgun email sending
3. Test all API endpoints
4. Set up development workflow

### 2. Adding Features
1. Gmail integration for receiving emails
2. Smart email routing and actions
3. Memory/context for conversations
4. Advanced analytics and monitoring

### 3. Production Preparation
1. Implement proper logging
2. Add comprehensive error handling
3. Set up monitoring and alerts
4. Configure secure credential management

---

This development setup provides a solid foundation for building intelligent email processing features while maintaining code quality and development velocity. 