# LLM Adapters

This directory contains adapters for various Large Language Model providers, implementing the unified `LLMProviderInterface`.

## Available Adapters

### Implemented
- **Gemini** (`gemini.py`): Google's Gemini models (1.5-pro, 1.5-flash)

### Planned
- **OpenAI** (`openai.py`): GPT-4, GPT-3.5-turbo
- **Anthropic** (`anthropic.py`): Claude 3 models
- **LangChain** (`langchain.py`): Complex chains and workflows
- **Azure OpenAI** (`azure_openai.py`): Enterprise Azure deployments
- **Cohere** (`cohere.py`): Cohere's language models
- **Local** (`local.py`): Self-hosted models (Ollama, vLLM, etc.)

## Adding a New Adapter

To add support for a new LLM provider:

1. Create a new file named `{provider}.py`
2. Implement the `LLMProviderInterface`
3. Handle provider-specific authentication and configuration
4. Implement all required methods with proper error handling

### Example Template

```python
from ...core.interfaces.llm_provider import (
    LLMProviderInterface,
    LLMConfig,
    LLMProvider,
    ClassificationResult,
    GenerationResult,
)

class NewProviderAdapter(LLMProviderInterface):
    """Adapter for NewProvider LLM."""
    
    def _validate_config(self) -> None:
        """Validate provider-specific configuration."""
        if self.config.provider != LLMProvider.NEW_PROVIDER:
            raise ValueError(f"Invalid provider: {self.config.provider}")
        
        # Add validation logic
    
    async def classify(self, text: str, categories: List[str], ...) -> ClassificationResult:
        """Implement classification logic."""
        # Provider-specific implementation
        pass
    
    async def generate(self, prompt: str, ...) -> GenerationResult:
        """Implement generation logic."""
        # Provider-specific implementation
        pass
    
    # Implement other required methods...
```

## Configuration

Each adapter requires specific configuration through `LLMConfig`:

```python
from core.interfaces.llm_provider import LLMConfig, LLMProvider

# Example configurations
gemini_config = LLMConfig(
    provider=LLMProvider.GOOGLE,
    model="gemini-1.5-pro",
    api_key="your-api-key",
    temperature=0.7,
    max_tokens=2000
)

openai_config = LLMConfig(
    provider=LLMProvider.OPENAI,
    model="gpt-4-turbo-preview",
    api_key="your-api-key",
    temperature=0.5,
    additional_params={
        "top_p": 0.9,
        "frequency_penalty": 0.1
    }
)
```

## Best Practices

1. **Error Handling**: Always provide graceful fallbacks
2. **Rate Limiting**: Implement provider-specific rate limits
3. **Token Counting**: Track token usage accurately
4. **Async Operations**: Use async/await for all API calls
5. **Retry Logic**: Implement exponential backoff for transient errors
6. **Cost Tracking**: Monitor API usage and costs

## Testing

Each adapter should have comprehensive tests:

```python
# tests/unit/adapters/llm/test_provider.py
async def test_classification():
    adapter = ProviderAdapter(config)
    result = await adapter.classify(
        text="Test email",
        categories=["spam", "not_spam"]
    )
    assert result.category in ["spam", "not_spam"]
    assert 0 <= result.confidence <= 1
``` 