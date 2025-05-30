"""
Abstract interface for email providers.

This interface defines the contract for email services (Gmail, Mailgun, Mailcow, etc.)
ensuring we can easily switch between providers.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any, AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class EmailProvider(str, Enum):
    """Supported email providers."""
    GMAIL = "gmail"
    MAILGUN = "mailgun"
    SENDGRID = "sendgrid"
    MAILCOW = "mailcow"
    EXCHANGE = "exchange"
    IMAP = "imap"


@dataclass
class EmailAddress:
    """Email address with optional name."""
    email: str
    name: Optional[str] = None
    
    def __str__(self) -> str:
        if self.name:
            return f"{self.name} <{self.email}>"
        return self.email


@dataclass
class EmailAttachment:
    """Email attachment metadata."""
    filename: str
    content_type: str
    size: int
    content_id: Optional[str] = None
    is_inline: bool = False
    data: Optional[bytes] = None  # Only loaded when needed


@dataclass
class Email:
    """Core email entity."""
    id: str
    thread_id: Optional[str]
    from_address: EmailAddress
    to_addresses: List[EmailAddress]
    cc_addresses: List[EmailAddress] = field(default_factory=list)
    bcc_addresses: List[EmailAddress] = field(default_factory=list)
    subject: str
    body_text: str
    body_html: Optional[str] = None
    date: datetime = field(default_factory=datetime.utcnow)
    attachments: List[EmailAttachment] = field(default_factory=list)
    headers: Dict[str, str] = field(default_factory=dict)
    labels: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def has_attachments(self) -> bool:
        """Check if email has attachments."""
        return len(self.attachments) > 0
    
    @property
    def sender_domain(self) -> str:
        """Extract sender's domain."""
        return self.from_address.email.split('@')[-1]


@dataclass
class EmailFilter:
    """Filters for querying emails."""
    labels: Optional[List[str]] = None
    from_address: Optional[str] = None
    to_address: Optional[str] = None
    subject_contains: Optional[str] = None
    body_contains: Optional[str] = None
    has_attachments: Optional[bool] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    unread_only: bool = False
    limit: int = 100


@dataclass
class EmailProviderConfig:
    """Configuration for email providers."""
    provider: EmailProvider
    credentials: Dict[str, Any]  # Provider-specific credentials
    webhook_url: Optional[str] = None
    polling_interval: int = 60  # seconds
    batch_size: int = 50
    additional_config: Dict[str, Any] = field(default_factory=dict)


class EmailProviderInterface(ABC):
    """Abstract interface for email providers."""
    
    def __init__(self, config: EmailProviderConfig):
        """Initialize the provider with configuration."""
        self.config = config
        self._validate_config()
    
    @abstractmethod
    def _validate_config(self) -> None:
        """Validate provider-specific configuration."""
        pass
    
    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to the email service."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to the email service."""
        pass
    
    @abstractmethod
    async def fetch_emails(
        self,
        filter: Optional[EmailFilter] = None
    ) -> List[Email]:
        """
        Fetch emails based on filter criteria.
        
        Args:
            filter: Optional filter criteria
            
        Returns:
            List of emails matching the criteria
        """
        pass
    
    @abstractmethod
    async def fetch_email_by_id(self, email_id: str) -> Email:
        """
        Fetch a specific email by ID.
        
        Args:
            email_id: The email identifier
            
        Returns:
            The requested email
        """
        pass
    
    @abstractmethod
    async def send_email(
        self,
        to: List[EmailAddress],
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
        cc: Optional[List[EmailAddress]] = None,
        bcc: Optional[List[EmailAddress]] = None,
        attachments: Optional[List[EmailAttachment]] = None,
        reply_to_id: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Send an email.
        
        Args:
            to: List of recipients
            subject: Email subject
            body_text: Plain text body
            body_html: Optional HTML body
            cc: Optional CC recipients
            bcc: Optional BCC recipients
            attachments: Optional attachments
            reply_to_id: Optional ID of email being replied to
            headers: Optional additional headers
            
        Returns:
            ID of the sent email
        """
        pass
    
    @abstractmethod
    async def create_draft(
        self,
        to: List[EmailAddress],
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
        cc: Optional[List[EmailAddress]] = None,
        bcc: Optional[List[EmailAddress]] = None,
        attachments: Optional[List[EmailAttachment]] = None,
        reply_to_id: Optional[str] = None
    ) -> str:
        """
        Create a draft email.
        
        Returns:
            ID of the created draft
        """
        pass
    
    @abstractmethod
    async def mark_as_read(self, email_ids: List[str]) -> None:
        """Mark emails as read."""
        pass
    
    @abstractmethod
    async def mark_as_unread(self, email_ids: List[str]) -> None:
        """Mark emails as unread."""
        pass
    
    @abstractmethod
    async def add_labels(
        self,
        email_ids: List[str],
        labels: List[str]
    ) -> None:
        """Add labels to emails."""
        pass
    
    @abstractmethod
    async def remove_labels(
        self,
        email_ids: List[str],
        labels: List[str]
    ) -> None:
        """Remove labels from emails."""
        pass
    
    @abstractmethod
    async def delete_emails(self, email_ids: List[str]) -> None:
        """Delete emails (move to trash)."""
        pass
    
    @abstractmethod
    async def setup_webhook(self, events: List[str]) -> str:
        """
        Setup webhook for real-time notifications.
        
        Args:
            events: List of events to subscribe to
            
        Returns:
            Webhook ID or subscription ID
        """
        pass
    
    @abstractmethod
    async def stream_emails(
        self,
        filter: Optional[EmailFilter] = None
    ) -> AsyncIterator[Email]:
        """
        Stream emails in real-time.
        
        Args:
            filter: Optional filter criteria
            
        Yields:
            Emails as they arrive
        """
        pass
    
    async def health_check(self) -> bool:
        """Check if the provider is available and working."""
        try:
            await self.connect()
            # Try to fetch one email
            await self.fetch_emails(EmailFilter(limit=1))
            await self.disconnect()
            return True
        except Exception:
            return False
    
    def get_info(self) -> Dict[str, Any]:
        """Get provider information."""
        return {
            "provider": self.config.provider.value,
            "webhook_url": self.config.webhook_url,
            "polling_interval": self.config.polling_interval,
        } 