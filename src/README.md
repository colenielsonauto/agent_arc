# Email Router - Source Code Architecture

## Overview

This directory contains the refactored email router system, designed with a **future-proof, AI-first architecture** that supports multiple LLM providers, email services, and advanced features like multi-agent workflows and long-term memory.

## Architecture Principles

1. **Hexagonal Architecture**: Core business logic is isolated from external dependencies
2. **Provider Agnostic**: Easy swapping of LLMs, email services, and storage systems
3. **Event-Driven**: Loose coupling through domain events
4. **Async-First**: Built for high concurrency and performance
5. **Security by Design**: Encryption, audit logging, and privacy controls

## Directory Structure

```
src/
├── core/               # Domain logic (provider-agnostic)
│   ├── entities/       # Domain models
│   ├── use_cases/      # Business logic
│   └── interfaces/     # Abstract interfaces
├── adapters/           # External integrations
│   ├── llm/            # LLM providers (OpenAI, Gemini, etc.)
│   ├── email/          # Email services (Gmail, Mailgun, etc.)
│   ├── memory/         # Storage systems (Redis, Pinecone, etc.)
│   └── analytics/      # Monitoring (Prometheus, Datadog, etc.)
├── agents/             # Multi-agent workflows
├── api/                # API layer
│   ├── rest/           # REST endpoints
│   ├── graphql/        # GraphQL schema
│   └── webhooks/       # Event handlers
├── infrastructure/     # Technical concerns
│   ├── config/         # Configuration management
│   ├── security/       # Security infrastructure
│   ├── monitoring/     # Observability
│   └── deployment/     # IaC and manifests
└── shared/             # Cross-cutting concerns
    ├── prompts/        # AI prompt templates
    ├── utils/          # Utilities
    └── exceptions/     # Custom exceptions
```

## Core Components

### 1. Interfaces (Ports)
Abstract interfaces that define contracts for external services:
- `LLMProviderInterface`: AI/LLM operations
- `EmailProviderInterface`: Email operations
- `MemoryStoreInterface`: Storage and retrieval
- `AnalyticsSinkInterface`: Monitoring and metrics

### 2. Use Cases
Business logic that orchestrates the system:
- `EmailClassifier`: Classifies emails using AI
- `EmailRouter`: Routes emails to appropriate teams
- `ResponseGenerator`: Generates email responses

### 3. Adapters
Concrete implementations of interfaces:
- **LLM**: Gemini, OpenAI, Anthropic, LangChain
- **Email**: Gmail, Mailgun, Mailcow
- **Memory**: Redis, Pinecone, PostgreSQL+pgvector
- **Analytics**: Prometheus, Datadog, LangSmith

## Key Features

### 🤖 Multi-LLM Support
```python
# Easy provider switching
llm_pool = LLMProviderPool([
    GeminiAdapter(gemini_config),
    OpenAIAdapter(openai_config),
    AnthropicAdapter(claude_config)
])

# Automatic fallback and load balancing
result = await llm_pool.execute_with_fallback(
    "classify", 
    email_text, 
    categories
)
```

### 🧠 Memory & Context
```python
# Store conversation context
await memory_store.update_conversation_context(
    ConversationContext(
        conversation_id=thread_id,
        user_id=user_id,
        messages=messages
    )
)

# Semantic search for similar emails
similar = await memory_store.search_memories(
    SearchQuery(
        query=email.content,
        user_id=user_id,
        similarity_threshold=0.8
    )
)
```

### 🤝 Multi-Agent Workflows
```python
# Complex email processing with multiple agents
orchestrator = EmailOrchestrator(
    agents=[
        ClassifierAgent(),
        ResearchAgent(),
        ResponseAgent()
    ]
)

result = await orchestrator.process_email(
    email,
    strategy="comprehensive"
)
```

### 📊 Comprehensive Analytics
```python
# Track everything with structured metrics
await analytics.track_email_processing(
    EmailProcessingMetrics(
        email_id=email.id,
        classification=result.category,
        confidence=result.confidence,
        processing_time_ms=duration,
        llm_provider="gemini",
        tokens_used=1234
    )
)
```

## Configuration

The system uses Pydantic for type-safe configuration:

```python
from infrastructure.config import get_settings

settings = get_settings()

# Access configuration
llm_config = settings.get_llm_config("openai")
email_config = settings.get_email_config("gmail")

# Feature flags
if settings.enable_memory:
    memory_store = create_memory_store(settings.memory)
```

## Security

Security is built into every layer:
- **Encryption**: All sensitive data encrypted at rest
- **Key Management**: Secure API key storage with Vault
- **Audit Logging**: Every action is logged
- **Privacy**: GDPR-compliant data handling

## Development

### Running Locally
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your settings

# Run tests
pytest tests/

# Start development server
python -m uvicorn api.main:app --reload
```

### Adding a New Provider

1. **Create Interface Implementation**:
```python
# adapters/llm/new_provider.py
class NewProviderAdapter(LLMProviderInterface):
    def _validate_config(self) -> None:
        # Validate configuration
        pass
    
    async def classify(self, ...):
        # Implement classification
        pass
```

2. **Add Configuration**:
```python
# infrastructure/config/settings.py
class LLMSettings(BaseSettings):
    new_provider_api_key: SecretStr = Field(None, env="NEW_PROVIDER_API_KEY")
```

3. **Register Provider**:
```python
# In your initialization code
providers.append(
    NewProviderAdapter(config)
)
```

## Testing

Comprehensive test coverage across all layers:
```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# End-to-end tests
pytest tests/e2e/

# Performance tests
pytest tests/performance/
```

## Deployment

Multiple deployment options:
- **Cloud Functions**: Serverless on GCP
- **Kubernetes**: Container orchestration
- **Docker Compose**: Local development
- **Terraform**: Infrastructure as Code

## Future Roadmap

1. **Enhanced AI Capabilities**
   - GPT-4 Vision for attachment processing
   - Voice transcription for voicemail-to-email
   - Multi-language support

2. **Advanced Routing**
   - ML-based routing optimization
   - Dynamic SLA adjustment
   - Team workload balancing

3. **Integration Expansion**
   - Slack/Teams notifications
   - CRM integration (Salesforce, HubSpot)
   - Calendar integration for meeting scheduling

4. **Analytics & Insights**
   - Email pattern analysis
   - Response time optimization
   - Customer sentiment tracking

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines on:
- Code style and standards
- Testing requirements
- Pull request process
- Architecture decisions 