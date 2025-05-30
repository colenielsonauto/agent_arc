"""
Google Gemini LLM adapter.

This adapter implements the LLMProviderInterface for Google's Gemini models,
providing a consistent interface for AI operations.
"""

import json
import asyncio
from typing import Dict, List, Optional, Any
import google.generativeai as genai
from datetime import datetime

from ...core.interfaces.llm_provider import (
    LLMProviderInterface,
    LLMConfig,
    LLMProvider,
    ClassificationResult,
    GenerationResult,
)


class GeminiAdapter(LLMProviderInterface):
    """Google Gemini adapter for LLM operations."""
    
    def _validate_config(self) -> None:
        """Validate Gemini-specific configuration."""
        if self.config.provider != LLMProvider.GOOGLE:
            raise ValueError(f"Invalid provider: {self.config.provider}")
        
        if not self.config.api_key:
            raise ValueError("Google API key is required")
        
        # Initialize Gemini
        genai.configure(api_key=self.config.api_key)
        
        # Validate model name
        valid_models = [
            "gemini-1.5-pro",
            "gemini-1.5-flash", 
            "gemini-pro",
            "gemini-pro-vision"
        ]
        if self.config.model not in valid_models:
            raise ValueError(f"Invalid model: {self.config.model}. Valid models: {valid_models}")
    
    async def classify(
        self,
        text: str,
        categories: List[str],
        examples: Optional[List[Dict[str, str]]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ClassificationResult:
        """Classify text using Gemini."""
        # Build the classification prompt
        prompt_parts = [
            "You are a classification expert. Classify the following text into one of the given categories.",
            f"\nCategories: {', '.join(categories)}",
            f"\nText: {text}"
        ]
        
        if examples:
            prompt_parts.insert(2, "\nExamples:")
            for ex in examples:
                prompt_parts.insert(3, f"- Text: {ex['text']} -> Category: {ex['category']}")
        
        if context:
            prompt_parts.append(f"\nAdditional context: {json.dumps(context)}")
        
        prompt_parts.append("\nRespond with a JSON object containing 'category' (the chosen category), 'confidence' (0-1), and 'reasoning' (brief explanation).")
        
        prompt = "\n".join(prompt_parts)
        
        # Generate classification
        start_time = datetime.utcnow()
        try:
            model = genai.GenerativeModel(self.config.model)
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                model.generate_content,
                prompt
            )
            
            # Parse response
            response_text = response.text.strip()
            
            # Try to parse as JSON
            try:
                result_data = json.loads(response_text)
                category = result_data.get("category", categories[0])
                confidence = float(result_data.get("confidence", 0.5))
                reasoning = result_data.get("reasoning", "")
            except json.JSONDecodeError:
                # Fallback: extract category from text
                category = categories[0]  # Default
                for cat in categories:
                    if cat.lower() in response_text.lower():
                        category = cat
                        break
                confidence = 0.7  # Default confidence for non-JSON response
                reasoning = response_text
            
            # Ensure category is valid
            if category not in categories:
                category = categories[0]
                confidence = 0.5
            
            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return ClassificationResult(
                category=category,
                confidence=confidence,
                reasoning=reasoning,
                metadata={
                    "model": self.config.model,
                    "duration_ms": duration_ms,
                    "raw_response": response_text
                }
            )
            
        except Exception as e:
            # Return a default classification on error
            return ClassificationResult(
                category=categories[0],
                confidence=0.0,
                reasoning=f"Classification failed: {str(e)}",
                metadata={"error": str(e)}
            )
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> GenerationResult:
        """Generate text using Gemini."""
        # Build the full prompt
        full_prompt_parts = []
        
        if system_prompt:
            full_prompt_parts.append(f"System: {system_prompt}")
        
        if context:
            full_prompt_parts.append(f"Context: {json.dumps(context)}")
        
        full_prompt_parts.append(prompt)
        
        full_prompt = "\n\n".join(full_prompt_parts)
        
        # Get generation parameters
        temperature = kwargs.get("temperature", self.config.temperature)
        max_tokens = kwargs.get("max_tokens", self.config.max_tokens)
        
        # Configure generation
        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            top_p=kwargs.get("top_p", 0.95),
            top_k=kwargs.get("top_k", 40),
        )
        
        # Generate
        start_time = datetime.utcnow()
        try:
            model = genai.GenerativeModel(self.config.model)
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: model.generate_content(
                    full_prompt,
                    generation_config=generation_config
                )
            )
            
            text = response.text
            # Estimate tokens (Gemini doesn't provide exact count in response)
            tokens_used = len(text.split()) * 1.3  # Rough estimate
            
            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return GenerationResult(
                text=text,
                tokens_used=int(tokens_used),
                model=self.config.model,
                metadata={
                    "duration_ms": duration_ms,
                    "temperature": temperature,
                    "finish_reason": "stop"
                }
            )
            
        except Exception as e:
            return GenerationResult(
                text=f"Generation failed: {str(e)}",
                tokens_used=0,
                model=self.config.model,
                metadata={"error": str(e)}
            )
    
    async def extract_structured(
        self,
        text: str,
        schema: Dict[str, Any],
        examples: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Extract structured data using Gemini."""
        # Build extraction prompt
        prompt_parts = [
            "Extract structured information from the following text according to the schema.",
            f"\nSchema: {json.dumps(schema, indent=2)}",
            f"\nText: {text}"
        ]
        
        if examples:
            prompt_parts.insert(2, "\nExamples:")
            for ex in examples:
                prompt_parts.insert(3, f"- Input: {ex['input']}\n  Output: {json.dumps(ex['output'])}")
        
        prompt_parts.append("\nRespond with a valid JSON object matching the schema.")
        
        prompt = "\n".join(prompt_parts)
        
        # Generate extraction
        result = await self.generate(prompt)
        
        # Parse the response
        try:
            # Try to extract JSON from the response
            response_text = result.text.strip()
            
            # Find JSON in the response (it might be wrapped in markdown)
            import re
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(1)
            
            extracted = json.loads(response_text)
            return extracted
            
        except json.JSONDecodeError:
            # Return empty dict on parse error
            return {}
    
    async def embed(
        self,
        texts: List[str],
        model: Optional[str] = None
    ) -> List[List[float]]:
        """Generate embeddings using Gemini."""
        # Note: Gemini doesn't have a dedicated embedding API yet
        # This is a placeholder that returns mock embeddings
        # In production, you might want to use a different service for embeddings
        
        import hashlib
        embeddings = []
        
        for text in texts:
            # Create a deterministic mock embedding based on text hash
            text_hash = hashlib.sha256(text.encode()).hexdigest()
            # Convert hash to a list of floats
            embedding = []
            for i in range(0, len(text_hash), 8):
                chunk = text_hash[i:i+8]
                value = int(chunk, 16) / (2**32) - 0.5  # Normalize to [-0.5, 0.5]
                embedding.append(value)
            
            # Pad or truncate to standard dimension (1536 for compatibility)
            embedding_dim = 1536
            if len(embedding) < embedding_dim:
                embedding.extend([0.0] * (embedding_dim - len(embedding)))
            else:
                embedding = embedding[:embedding_dim]
            
            embeddings.append(embedding)
        
        return embeddings
    
    async def health_check(self) -> bool:
        """Check if Gemini API is accessible."""
        try:
            # Try a simple generation
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                model.generate_content,
                "Say 'healthy' if you're working"
            )
            return "healthy" in response.text.lower()
        except Exception:
            return False 