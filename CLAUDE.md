# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a production-ready AI email router built with FastAPI that automatically classifies incoming emails using Claude 3.5 Sonnet, generates personalized auto-replies, and forwards emails to appropriate team members. It's designed as a template for agencies to deploy for multiple clients.

## Development Commands

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Start development server with auto-reload
python -m uvicorn app.main:app --port 8080 --reload

# Alternative: Run directly
python -m app.main
```

### Testing
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_webhook.py -v

# Test health endpoint
curl http://localhost:8080/health
```

### Code Quality
```bash
# Format code with black
black app/ tests/

# Type checking
mypy app/

# No specific linting command defined - use black for formatting
```

## Architecture

### Core Components

**FastAPI Application Structure:**
- `app/main.py` - FastAPI application entry point with health checks and CORS
- `app/routers/webhooks.py` - Core Mailgun webhook handler (`/webhooks/mailgun/inbound`)
- `app/services/` - Business logic services:
  - `classifier.py` - Claude 3.5 Sonnet email classification
  - `email_composer.py` - Auto-reply generation (customer acknowledgment + team analysis)
  - `email_sender.py` - Mailgun email sending
- `app/models/schemas.py` - Pydantic data models
- `app/utils/config.py` - Environment configuration management

### Email Processing Pipeline
1. Mailgun webhook receives email → `/webhooks/mailgun/inbound`
2. Background task processes email:
   - AI classification using Claude 3.5 Sonnet
   - Generate separate customer acknowledgment and team analysis
   - Send brief auto-reply to customer
   - Forward detailed analysis to appropriate team member

### Configuration Management
Environment variables are managed in `app/utils/config.py`:
- **Required:** `ANTHROPIC_API_KEY`, `MAILGUN_API_KEY`, `MAILGUN_DOMAIN`
- **Optional:** `ANTHROPIC_MODEL` (defaults to claude-3-5-sonnet-20241022), `PORT` (8080)

### Routing Rules
Team routing is configured in `app/routers/webhooks.py` in the `ROUTING_RULES` dictionary:
```python
ROUTING_RULES = {
    "support": "support@client.com",
    "billing": "billing@client.com", 
    "sales": "sales@client.com",
    "general": "general@client.com"
}
```

## Deployment

### Google Cloud Run (Primary)
```bash
gcloud run deploy email-router \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY},MAILGUN_API_KEY=${MAILGUN_API_KEY},MAILGUN_DOMAIN=${MAILGUN_DOMAIN}"
```

### Docker
The `Dockerfile` is optimized for Cloud Run deployment with minimal production dependencies.

## Client Customization

When deploying for new clients, customize:

1. **Routing Rules** in `app/routers/webhooks.py` - Update team email addresses
2. **Email Templates** in `app/utils/email_templates.py` - Brand styling and company info
3. **AI Prompts** in `app/services/classifier.py` - Adjust classification categories if needed
4. **Response Tone** in `app/services/email_composer.py` - Match client's voice and brand

## Key API Endpoints

- `GET /health` - Health check with component status
- `POST /webhooks/mailgun/inbound` - Main Mailgun webhook endpoint
- `GET /docs` - Interactive API documentation
- `GET /` - Service info and endpoint directory

## Testing Strategy

The test suite in `tests/test_webhook.py` covers:
- Health endpoint functionality
- Webhook endpoint with various data scenarios (valid, missing, empty)
- API documentation accessibility

Tests use environment variable mocking to avoid requiring actual API keys during testing.