# Email Router MVP - Setup Guide

## 🎯 Current Status

✅ **Completed**:
- New hexagonal architecture implemented
- Core interfaces and adapters created  
- Configuration management with Pydantic
- FastAPI application foundation
- Gmail and Gemini adapters
- Legacy code cleanup
- Test infrastructure

🚧 **Ready for Testing**: 
- MVP core functionality is implemented
- Need external service credentials to test

## 📋 Required Information

To get the MVP running, please provide the following:

### 1. **Google Gemini API** (Required)
```bash
# Get from: https://makersuite.google.com/app/apikey
GOOGLE_API_KEY=your_gemini_api_key_here
```

### 2. **Gmail API Credentials** (Required)
You need two files:
- **OAuth2 Client Credentials**: Download from Google Cloud Console
- **Access Token**: Generated during OAuth flow

**Steps to get credentials**:
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create/select a project
3. Enable Gmail API
4. Create OAuth2 credentials (Desktop application)
5. Download the JSON file → save as `.secrets/oauth_client.json`
6. Run OAuth flow to generate access token

### 3. **Environment Configuration** (Required)
Create `.env` file from `.env.example`:
```bash
cp .env.example .env
# Edit .env with your credentials
```

### 4. **Optional Services** (for full features)
- **Redis**: For memory/context storage
- **Monitoring**: Prometheus/Datadog for analytics

## 🚀 Quick Start Commands

### 1. Setup Environment
```bash
# Create environment file
cp .env.example .env

# Create secrets directory
mkdir -p .secrets

# Install dependencies
pip install -e ".[dev]"
```

### 2. Configure Services
```bash
# Edit .env file with your credentials
# At minimum, set:
# - GOOGLE_API_KEY
# - GMAIL_CREDENTIALS_PATH=.secrets/oauth_client.json
# - GMAIL_TOKEN_PATH=.secrets/token.json
```

### 3. Test Setup
```bash
# Run architecture test
python scripts/test_new_architecture.py

# Should show:
# ✅ Configuration loaded
# ✅ LLM provider health check passed  
# ✅ Email provider health check passed
```

### 4. Start API Server
```bash
# Start FastAPI development server
python -m uvicorn src.api.main:app --reload

# Test endpoints:
# http://localhost:8000/health
# http://localhost:8000/health/detailed
# http://localhost:8000/docs (API documentation)
```

## 🧪 Testing Endpoints

### Health Check
```bash
curl http://localhost:8000/health
```

### Detailed Health
```bash
curl http://localhost:8000/health/detailed
```

### Test Classification
```bash
curl -X POST "http://localhost:8000/test/classify" \
  -H "Content-Type: application/json" \
  -d '"I need help with my billing account"'
```

## 📁 File Structure Check

Required files that should exist:
```
├── .env                              # Your credentials
├── .secrets/
│   ├── oauth_client.json            # Gmail OAuth2 credentials
│   └── token.json                   # Gmail access token (auto-generated)
├── src/
│   ├── api/main.py                  # FastAPI application ✅
│   ├── core/                        # Domain logic ✅
│   ├── adapters/                    # External integrations ✅
│   └── infrastructure/config/       # Configuration ✅
├── pyproject.toml                   # Dependencies ✅
└── tasks/                           # Development roadmap ✅
```

## 🛠️ Troubleshooting

### Configuration Issues
```bash
# Test configuration loading
python -c "from src.infrastructure.config import get_settings; print(get_settings())"
```

### Import Issues
```bash
# Test imports
python -c "from src.adapters.llm.gemini import GeminiAdapter; print('✅ Imports work')"
```

### Gmail OAuth Setup
If you need help with Gmail OAuth2:
1. **Google Cloud Console** → APIs & Services → Credentials
2. Create **OAuth 2.0 Client ID** (Desktop application)
3. Download JSON file
4. Place in `.secrets/oauth_client.json`
5. Run the application - it will guide you through OAuth flow

### API Key Testing
```bash
# Test Gemini API key manually
python -c "
import google.generativeai as genai
genai.configure(api_key='YOUR_API_KEY')
model = genai.GenerativeModel('gemini-1.5-flash')
response = model.generate_content('Hello')
print(response.text)
"
```

## 📋 Next Steps After Setup

Once the MVP is running:

### Week 1 Tasks (Current)
- [ ] Get FastAPI server running
- [ ] Test LLM classification
- [ ] Test Gmail integration
- [ ] Validate health checks

### Week 2 Tasks
- [ ] Implement email processing pipeline
- [ ] Add webhook handlers
- [ ] Create routing logic
- [ ] Add error handling

### Week 3 Tasks  
- [ ] Deploy to Cloud Functions
- [ ] Add monitoring
- [ ] Performance testing
- [ ] Production configuration

## 🔍 Architecture Benefits

This new structure provides:

1. **Provider Agnostic**: Easy to swap LLMs, email services
2. **Testable**: Clean separation of concerns
3. **Scalable**: Ready for multi-agent workflows
4. **Maintainable**: Clear module boundaries
5. **Future-Proof**: Built for advanced AI features

## 📞 Support

If you run into issues:
1. Check the test script output: `python scripts/test_new_architecture.py`
2. Verify all required files exist
3. Check API endpoint responses
4. Review logs for specific errors

The MVP is designed to gracefully handle missing components and provide clear error messages for troubleshooting. 