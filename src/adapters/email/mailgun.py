"""
Mailgun email provider adapter.

This adapter implements the EmailProviderInterface for Mailgun,
providing a consistent interface for email operations using Mailgun's API.
"""

import asyncio
import re
from typing import List, Dict, Optional, Any, AsyncIterator
from datetime import datetime, timedelta
import logging
import json
import httpx
from urllib.parse import urljoin

from ...core.interfaces.email_provider import (
    EmailProviderInterface,
    EmailProviderConfig,
    EmailProvider,
    Email,
    EmailAddress,
    EmailAttachment,
    EmailFilter,
)

logger = logging.getLogger(__name__)


class MailgunAdapter(EmailProviderInterface):
    """Mailgun adapter for email operations."""
    
    def __init__(self, config: EmailProviderConfig):
        super().__init__(config)
        self.api_key = None
        self.domain = None
        self.base_url = "https://api.mailgun.net/v3"
        self.client = None
        self._webhook_id = None
    
    def _validate_config(self) -> None:
        """Validate Mailgun-specific configuration."""
        if self.config.provider != EmailProvider.MAILGUN:
            raise ValueError(f"Invalid provider: {self.config.provider}")
        
        # Check for required credentials
        required_keys = ["api_key", "domain"]
        for key in required_keys:
            if key not in self.config.credentials:
                raise ValueError(f"Missing required credential: {key}")
            
        if not self.config.credentials["api_key"]:
            raise ValueError("Mailgun API key cannot be empty")
            
        if not self.config.credentials["domain"]:
            raise ValueError("Mailgun domain cannot be empty")
    
    async def connect(self) -> None:
        """Connect to Mailgun API."""
        self.api_key = self.config.credentials["api_key"]
        self.domain = self.config.credentials["domain"]
        
        # Create HTTP client with authentication
        self.client = httpx.AsyncClient(
            auth=("api", self.api_key),
            timeout=30.0,
            base_url=self.base_url
        )
        
        # Test connection by getting domain info
        try:
            response = await self.client.get(f"/v3/domains/{self.domain}")
            response.raise_for_status()
            logger.info(f"Successfully connected to Mailgun domain: {self.domain}")
        except httpx.HTTPError as e:
            logger.error(f"Failed to connect to Mailgun: {e}")
            raise RuntimeError(f"Failed to connect to Mailgun: {e}")
    
    async def disconnect(self) -> None:
        """Disconnect from Mailgun API."""
        if self.client:
            await self.client.aclose()
            self.client = None
        self.api_key = None
        self.domain = None
        self._webhook_id = None
    
    async def fetch_emails(
        self,
        filter: Optional[EmailFilter] = None
    ) -> List[Email]:
        """
        Fetch emails from Mailgun.
        
        Note: Mailgun's API is primarily for sending emails. For receiving emails,
        you would typically use webhooks. This method provides basic functionality
        to list stored messages if available.
        """
        if not self.client:
            raise RuntimeError("Not connected to Mailgun API")
        
        # Mailgun doesn't store incoming emails by default
        # This would typically work with webhooks for receiving emails
        # For now, we'll return an empty list with a warning
        logger.warning(
            "Mailgun doesn't store incoming emails by default. "
            "Use webhooks for receiving emails."
        )
        return []
    
    async def fetch_email_by_id(self, email_id: str) -> Email:
        """
        Fetch a specific email by ID.
        
        Note: Mailgun doesn't store emails for retrieval unless configured
        to do so with store() action in routes.
        """
        if not self.client:
            raise RuntimeError("Not connected to Mailgun API")
        
        raise NotImplementedError(
            "Mailgun doesn't store emails by default. "
            "Configure store() action in routes to enable email storage."
        )
    
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
        """Send an email via Mailgun."""
        if not self.client:
            raise RuntimeError("Not connected to Mailgun API")
        
        # Prepare the email data
        data = {
            "from": f"postmaster@{self.domain}",
            "to": [str(addr) for addr in to],
            "subject": subject,
            "text": body_text,
        }
        
        # Add HTML body if provided
        if body_html:
            data["html"] = body_html
        
        # Add CC recipients
        if cc:
            data["cc"] = [str(addr) for addr in cc]
        
        # Add BCC recipients
        if bcc:
            data["bcc"] = [str(addr) for addr in bcc]
        
        # Add custom headers
        if headers:
            for key, value in headers.items():
                data[f"h:{key}"] = value
        
        # Add reply-to header
        if reply_to_id:
            data["h:In-Reply-To"] = reply_to_id
            data["h:References"] = reply_to_id
        
        # Prepare files for attachments
        files = []
        if attachments:
            for attachment in attachments:
                if attachment.data:
                    files.append(
                        ("attachment", (attachment.filename, attachment.data, attachment.content_type))
                    )
        
        try:
            # Send the email
            url = f"/v3/{self.domain}/messages"
            if files:
                response = await self.client.post(url, data=data, files=files)
            else:
                response = await self.client.post(url, data=data)
            
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"Email sent successfully: {result.get('id')}")
            return result.get("id", "unknown")
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to send email: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response: {e.response.text}")
            raise RuntimeError(f"Failed to send email: {e}")
    
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
        
        Note: Mailgun doesn't have a draft concept. This will store the draft
        information locally and return a draft ID.
        """
        # Mailgun doesn't support drafts - we could implement local storage
        # For now, just return a placeholder
        draft_id = f"draft-{datetime.utcnow().timestamp()}"
        logger.warning(f"Mailgun doesn't support drafts. Created local draft: {draft_id}")
        return draft_id
    
    async def mark_as_read(self, email_ids: List[str]) -> None:
        """Mark emails as read."""
        # Mailgun doesn't store emails by default, so this operation is not applicable
        logger.warning("Mailgun doesn't store emails by default. mark_as_read not applicable.")
    
    async def mark_as_unread(self, email_ids: List[str]) -> None:
        """Mark emails as unread."""
        # Mailgun doesn't store emails by default, so this operation is not applicable
        logger.warning("Mailgun doesn't store emails by default. mark_as_unread not applicable.")
    
    async def add_labels(
        self,
        email_ids: List[str],
        labels: List[str]
    ) -> None:
        """Add labels to emails."""
        # Mailgun doesn't store emails by default, so this operation is not applicable
        logger.warning("Mailgun doesn't store emails by default. add_labels not applicable.")
    
    async def remove_labels(
        self,
        email_ids: List[str],
        labels: List[str]
    ) -> None:
        """Remove labels from emails."""
        # Mailgun doesn't store emails by default, so this operation is not applicable
        logger.warning("Mailgun doesn't store emails by default. remove_labels not applicable.")
    
    async def delete_emails(self, email_ids: List[str]) -> None:
        """Delete emails."""
        # Mailgun doesn't store emails by default, so this operation is not applicable
        logger.warning("Mailgun doesn't store emails by default. delete_emails not applicable.")
    
    async def setup_webhook(self, events: List[str]) -> str:
        """
        Setup webhook for email events.
        
        Args:
            events: List of events to subscribe to (e.g., ['delivered', 'opened', 'clicked'])
            
        Returns:
            Webhook ID
        """
        if not self.client:
            raise RuntimeError("Not connected to Mailgun API")
        
        if not self.config.webhook_url:
            raise ValueError("Webhook URL not configured")
        
        # Mailgun webhook events
        webhook_data = {
            "url": self.config.webhook_url,
        }
        
        # Set up webhook for each event type
        webhook_ids = []
        valid_events = ["delivered", "opened", "clicked", "unsubscribed", "complained", "bounced", "dropped"]
        
        for event in events:
            if event not in valid_events:
                logger.warning(f"Unknown webhook event: {event}. Valid events: {valid_events}")
                continue
                
            try:
                response = await self.client.post(
                    f"/v3/domains/{self.domain}/webhooks/{event}",
                    data=webhook_data
                )
                response.raise_for_status()
                result = response.json()
                webhook_ids.append(f"{event}:{result.get('webhook', {}).get('url', 'unknown')}")
                logger.info(f"Webhook set up for {event}: {result}")
                
            except httpx.HTTPError as e:
                logger.error(f"Failed to setup webhook for {event}: {e}")
        
        webhook_id = ",".join(webhook_ids)
        self._webhook_id = webhook_id
        return webhook_id
    
    async def stream_emails(
        self,
        filter: Optional[EmailFilter] = None
    ) -> AsyncIterator[Email]:
        """
        Stream emails in real-time.
        
        Note: For Mailgun, this would typically be implemented using webhooks
        rather than polling. This is a placeholder implementation.
        """
        # This would typically be implemented with webhook handling
        # For now, we'll just yield nothing and log a warning
        logger.warning(
            "Mailgun email streaming should be implemented with webhooks. "
            "Set up webhook handlers to receive real-time email events."
        )
        return
        yield  # Make this a generator
    
    async def get_domain_info(self) -> Dict[str, Any]:
        """Get information about the Mailgun domain."""
        if not self.client:
            raise RuntimeError("Not connected to Mailgun API")
        
        try:
            response = await self.client.get(f"/v3/domains/{self.domain}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to get domain info: {e}")
            raise RuntimeError(f"Failed to get domain info: {e}")
    
    async def get_stats(self, event: str, start: datetime, end: datetime) -> Dict[str, Any]:
        """
        Get statistics for the domain.
        
        Args:
            event: Event type (e.g., 'sent', 'delivered', 'opened')
            start: Start date for statistics
            end: End date for statistics
        """
        if not self.client:
            raise RuntimeError("Not connected to Mailgun API")
        
        params = {
            "event": event,
            "start": start.strftime("%a, %d %b %Y %H:%M:%S %z"),
            "end": end.strftime("%a, %d %b %Y %H:%M:%S %z"),
        }
        
        try:
            response = await self.client.get(f"/v3/{self.domain}/stats/total", params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to get stats: {e}")
            raise RuntimeError(f"Failed to get stats: {e}")
    
    async def validate_email(self, email: str) -> Dict[str, Any]:
        """
        Validate an email address using Mailgun's validation API.
        
        Args:
            email: Email address to validate
            
        Returns:
            Validation result
        """
        if not self.client:
            raise RuntimeError("Not connected to Mailgun API")
        
        try:
            response = await self.client.get(
                "/v4/address/validate",
                params={"address": email}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to validate email: {e}")
            raise RuntimeError(f"Failed to validate email: {e}")
    
    def get_info(self) -> Dict[str, Any]:
        """Get provider information."""
        return {
            "provider": self.config.provider.value,
            "domain": self.domain,
            "base_url": self.base_url,
            "webhook_url": self.config.webhook_url,
            "polling_interval": self.config.polling_interval,
            "webhook_id": self._webhook_id,
        } 