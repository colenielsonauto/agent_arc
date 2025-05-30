"""
Adapters for external services.

This package contains concrete implementations of the core interfaces
for various external services like LLMs, email providers, storage systems,
and analytics platforms.
"""

# Adapter registry for dynamic loading
ADAPTER_REGISTRY = {
    "llm": {
        "gemini": "adapters.llm.gemini.GeminiAdapter",
        "openai": "adapters.llm.openai.OpenAIAdapter",
        "anthropic": "adapters.llm.anthropic.AnthropicAdapter",
    },
    "email": {
        "gmail": "adapters.email.gmail.GmailAdapter",
        "mailgun": "adapters.email.mailgun.MailgunAdapter",
    },
    "memory": {
        "redis": "adapters.memory.redis.RedisAdapter",
        "pinecone": "adapters.memory.pinecone.PineconeAdapter",
        "postgres": "adapters.memory.postgres_vector.PostgresVectorAdapter",
    },
    "analytics": {
        "prometheus": "adapters.analytics.prometheus.PrometheusAdapter",
        "datadog": "adapters.analytics.datadog.DatadogAdapter",
    },
}


def get_adapter_class(adapter_type: str, provider: str):
    """
    Dynamically load an adapter class.
    
    Args:
        adapter_type: Type of adapter (llm, email, memory, analytics)
        provider: Provider name (gemini, gmail, redis, etc.)
        
    Returns:
        Adapter class
        
    Raises:
        ValueError: If adapter not found
    """
    if adapter_type not in ADAPTER_REGISTRY:
        raise ValueError(f"Unknown adapter type: {adapter_type}")
    
    if provider not in ADAPTER_REGISTRY[adapter_type]:
        raise ValueError(f"Unknown {adapter_type} provider: {provider}")
    
    # Dynamic import
    module_path, class_name = ADAPTER_REGISTRY[adapter_type][provider].rsplit(".", 1)
    module = __import__(module_path, fromlist=[class_name])
    return getattr(module, class_name) 