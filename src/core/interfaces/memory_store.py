"""
Abstract interface for memory stores.

This interface defines the contract for memory/context storage systems
(Redis, Pinecone, PostgreSQL, etc.) to enable conversation history,
user preferences, and semantic search.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid


class MemoryStoreType(str, Enum):
    """Types of memory stores."""
    REDIS = "redis"
    PINECONE = "pinecone"
    WEAVIATE = "weaviate"
    POSTGRES_VECTOR = "postgres_vector"
    QDRANT = "qdrant"
    MILVUS = "milvus"
    IN_MEMORY = "in_memory"


@dataclass
class MemoryEntry:
    """A single memory entry."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    content: str = ""
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    ttl: Optional[int] = None  # Time to live in seconds
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "content": self.content,
            "embedding": self.embedding,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "ttl": self.ttl
        }


@dataclass
class ConversationContext:
    """Conversation context with history."""
    conversation_id: str
    user_id: str
    thread_id: Optional[str] = None
    messages: List[MemoryEntry] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def add_message(self, content: str, role: str = "user", **metadata) -> None:
        """Add a message to the conversation."""
        entry = MemoryEntry(
            user_id=self.user_id,
            content=content,
            metadata={"role": role, **metadata}
        )
        self.messages.append(entry)
        self.updated_at = datetime.utcnow()
    
    def get_context_window(self, max_messages: int = 10) -> List[MemoryEntry]:
        """Get the most recent messages for context."""
        return self.messages[-max_messages:]


@dataclass
class UserPreferences:
    """User preferences and settings."""
    user_id: str
    preferences: Dict[str, Any] = field(default_factory=dict)
    routing_rules: Dict[str, Any] = field(default_factory=dict)
    response_style: Dict[str, Any] = field(default_factory=dict)
    blocked_senders: List[str] = field(default_factory=list)
    vip_senders: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SearchQuery:
    """Query for semantic search."""
    query: str
    user_id: Optional[str] = None
    filters: Dict[str, Any] = field(default_factory=dict)
    limit: int = 10
    similarity_threshold: float = 0.7
    include_metadata: bool = True


@dataclass
class MemoryStoreConfig:
    """Configuration for memory stores."""
    store_type: MemoryStoreType
    connection_params: Dict[str, Any]
    embedding_dimension: int = 1536
    default_ttl: Optional[int] = None  # seconds
    index_name: Optional[str] = None
    namespace: Optional[str] = None


class MemoryStoreInterface(ABC):
    """Abstract interface for memory stores."""
    
    def __init__(self, config: MemoryStoreConfig):
        """Initialize the memory store with configuration."""
        self.config = config
        self._validate_config()
    
    @abstractmethod
    def _validate_config(self) -> None:
        """Validate store-specific configuration."""
        pass
    
    @abstractmethod
    async def connect(self) -> None:
        """Connect to the memory store."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the memory store."""
        pass
    
    @abstractmethod
    async def store_memory(
        self,
        entry: MemoryEntry,
        namespace: Optional[str] = None
    ) -> str:
        """
        Store a memory entry.
        
        Args:
            entry: The memory entry to store
            namespace: Optional namespace for organization
            
        Returns:
            ID of the stored entry
        """
        pass
    
    @abstractmethod
    async def retrieve_memory(
        self,
        memory_id: str,
        namespace: Optional[str] = None
    ) -> Optional[MemoryEntry]:
        """
        Retrieve a specific memory by ID.
        
        Args:
            memory_id: The memory ID
            namespace: Optional namespace
            
        Returns:
            The memory entry if found
        """
        pass
    
    @abstractmethod
    async def search_memories(
        self,
        query: SearchQuery
    ) -> List[Tuple[MemoryEntry, float]]:
        """
        Search memories using semantic similarity.
        
        Args:
            query: The search query
            
        Returns:
            List of (memory, similarity_score) tuples
        """
        pass
    
    @abstractmethod
    async def get_conversation_context(
        self,
        conversation_id: str,
        user_id: str
    ) -> Optional[ConversationContext]:
        """
        Get conversation context.
        
        Args:
            conversation_id: The conversation ID
            user_id: The user ID
            
        Returns:
            The conversation context if found
        """
        pass
    
    @abstractmethod
    async def update_conversation_context(
        self,
        context: ConversationContext
    ) -> None:
        """Update or create conversation context."""
        pass
    
    @abstractmethod
    async def get_user_preferences(
        self,
        user_id: str
    ) -> Optional[UserPreferences]:
        """
        Get user preferences.
        
        Args:
            user_id: The user ID
            
        Returns:
            User preferences if found
        """
        pass
    
    @abstractmethod
    async def update_user_preferences(
        self,
        preferences: UserPreferences
    ) -> None:
        """Update or create user preferences."""
        pass
    
    @abstractmethod
    async def delete_memories(
        self,
        memory_ids: List[str],
        namespace: Optional[str] = None
    ) -> int:
        """
        Delete memories by IDs.
        
        Args:
            memory_ids: List of memory IDs to delete
            namespace: Optional namespace
            
        Returns:
            Number of deleted entries
        """
        pass
    
    @abstractmethod
    async def clear_user_data(self, user_id: str) -> None:
        """Clear all data for a user (GDPR compliance)."""
        pass
    
    async def get_related_memories(
        self,
        memory_id: str,
        limit: int = 5
    ) -> List[Tuple[MemoryEntry, float]]:
        """Get memories related to a specific memory."""
        memory = await self.retrieve_memory(memory_id)
        if not memory:
            return []
        
        query = SearchQuery(
            query=memory.content,
            user_id=memory.user_id,
            limit=limit + 1  # Include self
        )
        
        results = await self.search_memories(query)
        # Filter out the original memory
        return [(m, s) for m, s in results if m.id != memory_id][:limit]
    
    async def get_user_history(
        self,
        user_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[MemoryEntry]:
        """Get user's memory history."""
        # This is a default implementation that uses search
        # Specific stores may override with more efficient methods
        query = SearchQuery(
            query="",  # Empty query
            user_id=user_id,
            limit=limit,
            similarity_threshold=0.0  # Get all
        )
        results = await self.search_memories(query)
        return [entry for entry, _ in results][offset:offset + limit]
    
    async def health_check(self) -> bool:
        """Check if the store is available and working."""
        try:
            await self.connect()
            # Try a simple operation
            test_entry = MemoryEntry(
                content="Health check",
                user_id="system"
            )
            entry_id = await self.store_memory(test_entry)
            await self.delete_memories([entry_id])
            await self.disconnect()
            return True
        except Exception:
            return False 