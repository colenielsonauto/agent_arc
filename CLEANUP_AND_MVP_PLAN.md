# Email Router - Cleanup & MVP Plan

## 🔍 Current State Analysis

### ✅ New Architecture (Completed)
- `src/core/` - Hexagonal architecture with interfaces and entities
- `src/adapters/` - LLM, email, memory, and analytics adapters  
- `src/infrastructure/` - Configuration and security infrastructure
- `pyproject.toml` - Modern dependency management
- Comprehensive README and documentation

### 🧹 Legacy Components (Needs Cleanup)

#### 1. **Old Cloud Function** - `functions/email_router/`
```
functions/email_router/
├── main.py           # Legacy pubsub handler - DELETE
├── requirements.txt  # Duplicate deps - DELETE  
└── .secrets         # Move to project root
```
**Action**: Delete entire directory, migrate secrets

#### 2. **Legacy Scripts** - `scripts/`
```
scripts/
├── test_gmail_auth.py    # Imports old email_router module - REFACTOR
├── watch_gmail.py        # Imports old email_router module - REFACTOR
├── smoke_test.py         # Imports old email_router module - REFACTOR
└── README.md             # Update for new architecture
```
**Action**: Refactor to use new src/ architecture

#### 3. **Legacy Dependencies** - `requirements.txt`
```
requirements.txt    # Old format - DELETE (using pyproject.toml)
```
**Action**: Delete (superseded by pyproject.toml)

#### 4. **Legacy Tests** - `tests/integration/`
```
tests/integration/
├── test_full_pipeline.py  # Uses old imports - REFACTOR
└── test_listener.py       # Uses old imports - REFACTOR  
```
**Action**: Refactor to test new architecture

## 🎯 MVP Development Plan

### Phase 1: Core Integration (Week 1)
**Goal**: Get basic email processing working with new architecture

#### Tasks:
1. **API Layer Foundation**
   - [ ] Create `src/api/main.py` - FastAPI app
   - [ ] Add basic health check endpoints
   - [ ] Implement email webhook receiver

2. **Configuration Loading**
   - [ ] Test `src/infrastructure/config/settings.py`
   - [ ] Create `.env.example` updates
   - [ ] Validate all config loading

3. **Basic Integration**
   - [ ] Connect Gmail adapter to config
   - [ ] Connect Gemini adapter to config
   - [ ] Test email classification pipeline

### Phase 2: Working Pipeline (Week 2)
**Goal**: End-to-end email processing

#### Tasks:
1. **Email Processing Pipeline**
   - [ ] Implement `src/api/webhooks/gmail.py`
   - [ ] Connect classifier use case
   - [ ] Add basic routing logic

2. **Testing Infrastructure**
   - [ ] Refactor `scripts/test_gmail_auth.py`
   - [ ] Create integration tests for new architecture
   - [ ] Add unit tests for adapters

3. **Deployment Preparation**
   - [ ] Update Cloud Function deployment
   - [ ] Update Docker configuration
   - [ ] Test local development setup

### Phase 3: Production Ready (Week 3)
**Goal**: Stable MVP deployment

#### Tasks:
1. **Monitoring & Observability**
   - [ ] Implement basic analytics sink
   - [ ] Add structured logging
   - [ ] Health check endpoints

2. **Error Handling**
   - [ ] Comprehensive error handling
   - [ ] Retry mechanisms
   - [ ] Fallback strategies

3. **Documentation**
   - [ ] API documentation
   - [ ] Deployment guides
   - [ ] Configuration reference

## 📋 Required External Service Information

### 1. **Google Cloud Setup**
```bash
# Required Information:
- Google Cloud Project ID
- Service Account Key (JSON)
- Gmail API OAuth2 Credentials
- Pub/Sub Topic Name
- Cloud Function Region
```

### 2. **LLM Providers**
```bash
# Google Gemini
GOOGLE_API_KEY=your_gemini_api_key

# OpenAI (optional)
OPENAI_API_KEY=your_openai_key
OPENAI_ORG_ID=your_org_id

# Anthropic (optional)  
ANTHROPIC_API_KEY=your_claude_key
```

### 3. **Storage & Memory (Choose One)**
```bash
# Redis (recommended for MVP)
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD=your_redis_password

# OR Pinecone
PINECONE_API_KEY=your_pinecone_key
PINECONE_ENVIRONMENT=us-east-1

# OR PostgreSQL
DATABASE_URL=postgresql://user:pass@localhost/emailrouter
```

### 4. **Monitoring (Optional for MVP)**
```bash
# Prometheus
PROMETHEUS_PUSHGATEWAY=http://localhost:9091

# Datadog
DATADOG_API_KEY=your_datadog_key
DATADOG_APP_KEY=your_datadog_app_key
```

### 5. **Security**
```bash
# JWT Secret (generate random string)
JWT_SECRET=your_256_bit_secret

# Encryption Key (optional)
ENCRYPTION_KEY=your_encryption_key
```

## 🚀 Quick Start Commands

### 1. Cleanup Legacy Code
```bash
# Remove legacy components
rm -rf functions/email_router/
rm requirements.txt

# Create tasks directory
mkdir tasks
```

### 2. Environment Setup
```bash
# Copy environment template
cp .env.example .env
# Edit .env with your credentials

# Install dependencies
pip install -e ".[dev]"
```

### 3. Test New Architecture
```bash
# Run basic tests
pytest tests/unit/

# Test configuration loading
python -c "from src.infrastructure.config import get_settings; print(get_settings())"
```

## 📁 Task Organization Structure

After cleanup, create organized task tracking:

```
tasks/
├── mvp/
│   ├── week1_core_integration.md
│   ├── week2_pipeline.md  
│   └── week3_production.md
├── future/
│   ├── multi_agent_system.md
│   ├── advanced_memory.md
│   └── enterprise_features.md
└── maintenance/
    ├── dependency_updates.md
    ├── security_audits.md
    └── performance_optimization.md
``` 