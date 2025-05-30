# Week 1: Core Integration

**Goal**: Get basic email processing working with new architecture

## 🎯 Priority Tasks

### Day 1-2: API Foundation
- [ ] **Create FastAPI app** (`src/api/main.py`)
  - Basic FastAPI application
  - Health check endpoints
  - CORS configuration
  - Environment validation

- [ ] **Configuration Testing**
  - Test settings loading from `.env`
  - Validate all provider configurations
  - Test secret handling

- [ ] **Basic Gmail Integration**
  - Test OAuth2 flow
  - Validate Gmail API permissions
  - Test basic email fetching

### Day 3-4: LLM Integration
- [ ] **Gemini Adapter Testing**
  - Test API key authentication
  - Validate classification functionality
  - Test error handling and retries

- [ ] **Email Classification Pipeline**
  - Connect Gmail → Classifier
  - Test with real emails
  - Basic routing logic

### Day 5-7: Integration Testing
- [ ] **End-to-End Testing**
  - Gmail webhook → Classification → Response
  - Error handling and logging
  - Performance testing

- [ ] **Documentation**
  - Setup instructions
  - Configuration guide
  - Troubleshooting

## 📋 Prerequisites

### Required Environment Variables
```bash
# Google Cloud & Gmail
GOOGLE_API_KEY=your_gemini_api_key
GMAIL_CREDENTIALS_PATH=.secrets/oauth_client.json
GMAIL_TOKEN_PATH=.secrets/token.json

# Application
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# Security (generate these)
JWT_SECRET=your_256_bit_secret
```

### Required Files
- `.secrets/oauth_client.json` - Gmail OAuth2 credentials
- `.secrets/token.json` - Gmail access token (generated after auth)

## 🚧 Potential Blockers

1. **Gmail API Setup**
   - OAuth2 consent screen approval
   - API quotas and limits
   - Webhook endpoint requirements

2. **Gemini API**
   - API key access
   - Rate limiting
   - Model availability

3. **Local Development**
   - HTTPS requirements for OAuth
   - Port forwarding for webhooks
   - Environment consistency

## ✅ Definition of Done

- [ ] FastAPI app starts without errors
- [ ] Gmail API authentication works
- [ ] Gemini classification returns results
- [ ] Basic email processing pipeline works
- [ ] Comprehensive error handling
- [ ] All tests pass 