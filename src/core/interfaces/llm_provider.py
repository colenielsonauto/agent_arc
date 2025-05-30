"""
Abstract interface for LLM providers.

This interface defines the contract that all LLM providers (OpenAI, Anthropic, Google, etc.)
must implement, ensuring provider-agnostic AI integration.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import asyncio


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    AZURE_OPENAI = "azure_openai"
    COHERE = "cohere"
    LOCAL = "local"  # For self-hosted models


@dataclass
class ClassificationResult:
    """Result of email classification."""
    category: str
    confidence: float
    reasoning: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class GenerationResult:
    """Result of text generation."""
    text: str
    tokens_used: int
    model: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class LLMConfig:
    """Configuration for LLM providers."""
    provider: LLMProvider
    model: str
    api_key: Optional[str] = None
    endpoint: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    timeout: int = 30
    retry_attempts: int = 3
    additional_params: Optional[Dict[str, Any]] = None


class LLMProviderInterface(ABC):
    """Abstract interface for LLM providers."""
    
    def __init__(self, config: LLMConfig):
        """Initialize the provider with configuration."""
        self.config = config
        self._validate_config()
    
    @abstractmethod
    def _validate_config(self) -> None:
        """Validate provider-specific configuration."""
        pass
    
    @abstractmethod
    async def classify(
        self,
        text: str,
        categories: List[str],
        examples: Optional[List[Dict[str, str]]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ClassificationResult:
        """
        Classify text into one of the provided categories.
        
        Args:
            text: The text to classify
            categories: List of possible categories
            examples: Optional few-shot examples
            context: Optional additional context
            
        Returns:
            ClassificationResult with category and confidence
        """
        pass
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> GenerationResult:
        """
        Generate text based on a prompt.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            context: Optional additional context
            **kwargs: Provider-specific parameters
            
        Returns:
            GenerationResult with generated text and metadata
        """
        pass
    
    @abstractmethod
    async def extract_structured(
        self,
        text: str,
        schema: Dict[str, Any],
        examples: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Extract structured data from text according to schema.
        
        Args:
            text: The text to extract from
            schema: JSON schema or Pydantic model describing desired output
            examples: Optional examples of extraction
            
        Returns:
            Extracted data matching the schema
        """
        pass
    
    @abstractmethod
    async def embed(
        self,
        texts: List[str],
        model: Optional[str] = None
    ) -> List[List[float]]:
        """
        Generate embeddings for texts.
        
        Args:
            texts: List of texts to embed
            model: Optional embedding model to use
            
        Returns:
            List of embedding vectors
        """
        pass
    
    async def health_check(self) -> bool:
        """Check if the provider is available and working."""
        try:
            # Simple test generation
            result = await self.generate("Hello", timeout=5)
            return bool(result.text)
        except Exception:
            return False
    
    def get_info(self) -> Dict[str, Any]:
        """Get provider information."""
        return {
            "provider": self.config.provider.value,
            "model": self.config.model,
            "endpoint": self.config.endpoint,
        }


class LLMProviderPool:
    """
    Manages multiple LLM providers with load balancing and fallback.
    """
    
    def __init__(self, providers: List[LLMProviderInterface]):
        """Initialize the pool with a list of providers."""
        self.providers = providers
        self._provider_health: Dict[str, bool] = {}
        self._current_index = 0
    
    async def initialize(self) -> None:
        """Initialize the pool and check provider health."""
        health_checks = await asyncio.gather(
            *[provider.health_check() for provider in self.providers],
            return_exceptions=True
        )
        
        for provider, health in zip(self.providers, health_checks):
            self._provider_health[provider.get_info()["provider"]] = (
                health is True
            )
    
    async def get_optimal_provider(self) -> LLMProviderInterface:
        """Get the best available provider based on health and load."""
        healthy_providers = [
            p for p in self.providers
            if self._provider_health.get(p.get_info()["provider"], True)
        ]
        
        if not healthy_providers:
            raise RuntimeError("No healthy LLM providers available")
        
        # Simple round-robin for now
        provider = healthy_providers[self._current_index % len(healthy_providers)]
        self._current_index += 1
        
        return provider
    
    async def get_fallback_provider(self) -> LLMProviderInterface:
        """Get a fallback provider when primary fails."""
        # Try to find a different healthy provider
        current_provider = await self.get_optimal_provider()
        
        for provider in self.providers:
            if (provider != current_provider and 
                self._provider_health.get(provider.get_info()["provider"], True)):
                return provider
        
        raise RuntimeError("No fallback LLM provider available")
    
    async def execute_with_fallback(
        self,
        operation: str,
        *args,
        **kwargs
    ) -> Any:
        """Execute an operation with automatic fallback."""
        primary = await self.get_optimal_provider()
        
        try:
            method = getattr(primary, operation)
            return await method(*args, **kwargs)
        except Exception as e:
            # Log the error
            print(f"Primary provider failed: {e}")
            
            # Try fallback
            fallback = await self.get_fallback_provider()
            method = getattr(fallback, operation)
            return await method(*args, **kwargs) 