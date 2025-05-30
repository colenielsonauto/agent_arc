# Memory Store Adapters

This directory contains adapters for various memory/vector storage systems, implementing the unified `MemoryStoreInterface`.

## Purpose

Memory stores enable:
- **Conversation Context**: Track email threads and conversations
- **User Preferences**: Store and retrieve user-specific settings
- **Semantic Search**: Find similar emails and patterns
- **Historical Analysis**: Learn from past interactions
- **GDPR Compliance**: Manage user data lifecycle

## Planned Adapters

### Redis Stack (`redis.py`)
- In-memory storage with persistence
- Vector search capabilities via RediSearch
- Ideal for: Fast access, caching, real-time operations
- Features: TTL support, pub/sub, transactions

### Pinecone (`pinecone.py`)
- Managed vector database
- Ideal for: Large-scale similarity search
- Features: Serverless, metadata filtering, namespaces

### PostgreSQL + pgvector (`postgres_vector.py`)
- Hybrid relational + vector storage
- Ideal for: Complex queries, ACID compliance
- Features: SQL queries, joins with business data

### Weaviate (`weaviate.py`)
- Open-source vector database
- Ideal for: Semantic search, knowledge graphs
- Features: GraphQL API, automatic schema

### Qdrant (`qdrant.py`)
- High-performance vector search
- Ideal for: Real-time recommendations
- Features: Filtering, payload storage

### In-Memory (`in_memory.py`)
- Simple dictionary-based storage
- Ideal for: Testing, development
- Features: No external dependencies

## Implementation Guide

```python
from ...core.interfaces.memory_store import (
    MemoryStoreInterface,
    MemoryStoreConfig,
    MemoryEntry,
    ConversationContext,
    UserPreferences,
)

class NewMemoryAdapter(MemoryStoreInterface):
    """Adapter for NewMemoryStore."""
    
    def _validate_config(self) -> None:
        """Validate store-specific configuration."""
        # Validate connection params, credentials, etc.
        pass
    
    async def connect(self) -> None:
        """Establish connection to the store."""
        # Initialize client, create indexes, etc.
        pass
    
    async def store_memory(self, entry: MemoryEntry, namespace: Optional[str] = None) -> str:
        """Store a memory entry with embedding."""
        # Store entry with vector indexing
        pass
    
    # Implement other required methods...
```

## Configuration Examples

```python
# Redis configuration
redis_config = MemoryStoreConfig(
    store_type=MemoryStoreType.REDIS,
    connection_params={
        "host": "localhost",
        "port": 6379,
        "password": "your-password",
        "decode_responses": True
    },
    embedding_dimension=1536,
    default_ttl=86400  # 24 hours
)

# Pinecone configuration
pinecone_config = MemoryStoreConfig(
    store_type=MemoryStoreType.PINECONE,
    connection_params={
        "api_key": "your-api-key",
        "environment": "us-east-1"
    },
    index_name="email-memories",
    namespace="production"
)

# PostgreSQL configuration
postgres_config = MemoryStoreConfig(
    store_type=MemoryStoreType.POSTGRES_VECTOR,
    connection_params={
        "host": "localhost",
        "port": 5432,
        "database": "email_router",
        "user": "postgres",
        "password": "your-password"
    },
    embedding_dimension=1536
)
```

## Usage Patterns

### Storing Email Context
```python
# Store classification result
memory = MemoryEntry(
    user_id=user_id,
    content=f"{email.subject}\n{email.body_text[:500]}",
    embedding=await llm.embed([email.body_text])[0],
    metadata={
        "type": "email_classification",
        "category": classification.category,
        "confidence": classification.confidence
    }
)
await memory_store.store_memory(memory)
```

### Semantic Search
```python
# Find similar emails
query = SearchQuery(
    query="billing issue with subscription",
    user_id=user_id,
    limit=5,
    similarity_threshold=0.8
)
similar_emails = await memory_store.search_memories(query)
```

### User Preferences
```python
# Store user routing preferences
preferences = UserPreferences(
    user_id=user_id,
    routing_rules={
        "urgent_to_phone": True,
        "vip_priority": ["ceo@company.com"]
    },
    response_style={
        "tone": "professional",
        "brevity": "concise"
    }
)
await memory_store.update_user_preferences(preferences)
```

## Best Practices

1. **Embedding Management**: 
   - Cache embeddings to avoid recomputation
   - Use appropriate embedding models for your use case
   - Consider dimensionality reduction for large-scale deployments

2. **Data Lifecycle**:
   - Implement TTL for temporary data
   - Regular cleanup of old memories
   - GDPR-compliant data deletion

3. **Performance**:
   - Batch operations when possible
   - Use appropriate indexes
   - Monitor query performance

4. **Security**:
   - Encrypt sensitive data
   - Use secure connections
   - Implement access controls 