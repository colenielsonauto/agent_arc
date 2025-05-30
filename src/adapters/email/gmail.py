"""
Gmail email provider adapter.

This adapter implements the EmailProviderInterface for Gmail,
providing a consistent interface for email operations.
"""

import base64
import re
import os
import asyncio
from typing import List, Dict, Optional, Any, AsyncIterator
from datetime import datetime
import logging

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

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


class GmailAdapter(EmailProviderInterface):
    """Gmail adapter for email operations."""
    
    def __init__(self, config: EmailProviderConfig):
        super().__init__(config)
        self.service = None
        self.creds = None
        self._watch_id = None
    
    def _validate_config(self) -> None:
        """Validate Gmail-specific configuration."""
        if self.config.provider != EmailProvider.GMAIL:
            raise ValueError(f"Invalid provider: {self.config.provider}")
        
        # Check for required credentials
        required_keys = ["token_path", "scopes"]
        for key in required_keys:
            if key not in self.config.credentials:
                raise ValueError(f"Missing required credential: {key}")
    
    async def connect(self) -> None:
        """Connect to Gmail API."""
        await asyncio.get_event_loop().run_in_executor(
            None, self._connect_sync
        )
    
    def _connect_sync(self) -> None:
        """Synchronous connection logic."""
        token_path = self.config.credentials.get("token_path")
        client_secret_path = self.config.credentials.get("client_secret_path")
        scopes = self.config.credentials.get("scopes", [
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/gmail.send",
            "https://www.googleapis.com/auth/gmail.compose",
            "https://www.googleapis.com/auth/gmail.modify"
        ])
        
        # Load credentials
        if os.path.exists(token_path):
            self.creds = Credentials.from_authorized_user_file(token_path, scopes)
        
        # Refresh if needed
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
                # Save refreshed credentials
                with open(token_path, 'w') as token:
                    token.write(self.creds.to_json())
            else:
                raise RuntimeError(
                    "No valid credentials available. "
                    "Please run the OAuth flow to generate credentials."
                )
        
        # Build service
        self.service = build('gmail', 'v1', credentials=self.creds)
        logger.info("Successfully connected to Gmail API")
    
    async def disconnect(self) -> None:
        """Disconnect from Gmail API."""
        self.service = None
        self.creds = None
        self._watch_id = None
    
    async def fetch_emails(
        self,
        filter: Optional[EmailFilter] = None
    ) -> List[Email]:
        """Fetch emails from Gmail."""
        if not self.service:
            raise RuntimeError("Not connected to Gmail API")
        
        # Build query
        query_parts = []
        
        if filter:
            if filter.labels:
                for label in filter.labels:
                    query_parts.append(f"label:{label}")
            
            if filter.from_address:
                query_parts.append(f"from:{filter.from_address}")
            
            if filter.to_address:
                query_parts.append(f"to:{filter.to_address}")
            
            if filter.subject_contains:
                query_parts.append(f"subject:{filter.subject_contains}")
            
            if filter.body_contains:
                query_parts.append(f'"{filter.body_contains}"')
            
            if filter.has_attachments:
                query_parts.append("has:attachment")
            
            if filter.unread_only:
                query_parts.append("is:unread")
            
            if filter.date_from:
                query_parts.append(f"after:{filter.date_from.strftime('%Y/%m/%d')}")
            
            if filter.date_to:
                query_parts.append(f"before:{filter.date_to.strftime('%Y/%m/%d')}")
        
        query = " ".join(query_parts) if query_parts else None
        max_results = filter.limit if filter else 100
        
        # Fetch message IDs
        messages = await self._list_messages(query, max_results)
        
        # Fetch full messages
        emails = []
        for msg in messages:
            try:
                email = await self.fetch_email_by_id(msg['id'])
                emails.append(email)
            except Exception as e:
                logger.error(f"Error fetching email {msg['id']}: {e}")
        
        return emails
    
    async def _list_messages(
        self,
        query: Optional[str] = None,
        max_results: int = 100
    ) -> List[Dict[str, Any]]:
        """List message IDs matching query."""
        def list_sync():
            results = []
            page_token = None
            
            while len(results) < max_results:
                try:
                    response = self.service.users().messages().list(
                        userId='me',
                        q=query,
                        maxResults=min(max_results - len(results), 100),
                        pageToken=page_token
                    ).execute()
                    
                    messages = response.get('messages', [])
                    results.extend(messages)
                    
                    page_token = response.get('nextPageToken')
                    if not page_token:
                        break
                        
                except HttpError as e:
                    logger.error(f"Error listing messages: {e}")
                    break
            
            return results
        
        return await asyncio.get_event_loop().run_in_executor(
            None, list_sync
        )
    
    async def fetch_email_by_id(self, email_id: str) -> Email:
        """Fetch a specific email by ID."""
        def fetch_sync():
            msg = self.service.users().messages().get(
                userId='me',
                id=email_id,
                format='full'
            ).execute()
            
            return self._parse_gmail_message(msg)
        
        return await asyncio.get_event_loop().run_in_executor(
            None, fetch_sync
        )
    
    def _parse_gmail_message(self, msg: Dict[str, Any]) -> Email:
        """Parse Gmail API message into Email object."""
        payload = msg.get('payload', {})
        headers = payload.get('headers', [])
        
        # Extract headers
        header_dict = {h['name'].lower(): h['value'] for h in headers}
        
        # Parse addresses
        from_address = self._parse_email_address(header_dict.get('from', ''))
        to_addresses = self._parse_email_addresses(header_dict.get('to', ''))
        cc_addresses = self._parse_email_addresses(header_dict.get('cc', ''))
        bcc_addresses = self._parse_email_addresses(header_dict.get('bcc', ''))
        
        # Extract body
        body_text, body_html = self._extract_body(payload)
        
        # Extract attachments
        attachments = self._extract_attachments(payload)
        
        # Parse date
        date_str = header_dict.get('date', '')
        try:
            from email.utils import parsedate_to_datetime
            date = parsedate_to_datetime(date_str)
        except:
            date = datetime.utcnow()
        
        # Get labels
        labels = msg.get('labelIds', [])
        
        return Email(
            id=msg['id'],
            thread_id=msg.get('threadId'),
            from_address=from_address,
            to_addresses=to_addresses,
            cc_addresses=cc_addresses,
            bcc_addresses=bcc_addresses,
            subject=header_dict.get('subject', ''),
            body_text=body_text,
            body_html=body_html,
            date=date,
            attachments=attachments,
            headers=dict(headers),
            labels=labels,
            metadata={
                'snippet': msg.get('snippet', ''),
                'historyId': msg.get('historyId', ''),
                'internalDate': msg.get('internalDate', '')
            }
        )
    
    def _parse_email_address(self, address_str: str) -> EmailAddress:
        """Parse email address from string."""
        if not address_str:
            return EmailAddress(email="unknown@domain.com")
        
        # Extract email from "Name <email>" format
        match = re.search(r'([^<]*)<([^>]+)>', address_str)
        if match:
            name = match.group(1).strip().strip('"')
            email = match.group(2).strip()
            return EmailAddress(email=email, name=name if name else None)
        else:
            return EmailAddress(email=address_str.strip())
    
    def _parse_email_addresses(self, addresses_str: str) -> List[EmailAddress]:
        """Parse multiple email addresses from string."""
        if not addresses_str:
            return []
        
        addresses = []
        for addr in addresses_str.split(','):
            addresses.append(self._parse_email_address(addr.strip()))
        
        return addresses
    
    def _extract_body(self, payload: Dict[str, Any]) -> tuple[str, Optional[str]]:
        """Extract text and HTML body from message payload."""
        text_body = ""
        html_body = None
        
        # Single part message
        if 'body' in payload and 'data' in payload['body']:
            content = self._decode_base64(payload['body']['data'])
            mime_type = payload.get('mimeType', '')
            
            if mime_type == 'text/plain':
                text_body = content
            elif mime_type == 'text/html':
                html_body = content
                text_body = self._strip_html(content)
        
        # Multipart message
        if 'parts' in payload:
            for part in payload['parts']:
                mime_type = part.get('mimeType', '')
                
                if mime_type == 'text/plain' and 'body' in part and 'data' in part['body']:
                    text_body = self._decode_base64(part['body']['data'])
                elif mime_type == 'text/html' and 'body' in part and 'data' in part['body']:
                    html_body = self._decode_base64(part['body']['data'])
                    if not text_body:
                        text_body = self._strip_html(html_body)
                elif mime_type.startswith('multipart/') and 'parts' in part:
                    # Recursive extraction for nested parts
                    nested_text, nested_html = self._extract_body(part)
                    if nested_text and not text_body:
                        text_body = nested_text
                    if nested_html and not html_body:
                        html_body = nested_html
        
        return text_body.strip(), html_body
    
    def _extract_attachments(self, payload: Dict[str, Any]) -> List[EmailAttachment]:
        """Extract attachments from message payload."""
        attachments = []
        
        def process_parts(parts):
            for part in parts:
                filename = part.get('filename', '')
                if filename:
                    attachments.append(EmailAttachment(
                        filename=filename,
                        content_type=part.get('mimeType', ''),
                        size=int(part.get('body', {}).get('size', 0)),
                        content_id=part.get('body', {}).get('attachmentId')
                    ))
                
                # Check nested parts
                if 'parts' in part:
                    process_parts(part['parts'])
        
        if 'parts' in payload:
            process_parts(payload['parts'])
        
        return attachments
    
    def _decode_base64(self, data: str) -> str:
        """Decode base64url encoded data."""
        try:
            # Add padding if needed
            padding = 4 - (len(data) % 4)
            if padding != 4:
                data += '=' * padding
            
            decoded = base64.urlsafe_b64decode(data)
            return decoded.decode('utf-8', errors='ignore')
        except Exception as e:
            logger.error(f"Error decoding base64: {e}")
            return ""
    
    def _strip_html(self, html: str) -> str:
        """Remove HTML tags from text."""
        clean = re.compile('<.*?>')
        return re.sub(clean, '', html)
    
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
        """Send an email via Gmail."""
        if not self.service:
            raise RuntimeError("Not connected to Gmail API")
        
        # Create message
        message = self._create_message(
            to, subject, body_text, body_html,
            cc, bcc, attachments, reply_to_id, headers
        )
        
        # Send message
        def send_sync():
            result = self.service.users().messages().send(
                userId='me',
                body={'raw': message}
            ).execute()
            return result['id']
        
        return await asyncio.get_event_loop().run_in_executor(
            None, send_sync
        )
    
    def _create_message(
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
        """Create a message for sending."""
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        from email.mime.base import MIMEBase
        from email import encoders
        
        # Create message container
        if body_html or attachments:
            message = MIMEMultipart('alternative')
        else:
            message = MIMEText(body_text)
            message['Subject'] = subject
            message['To'] = ', '.join(str(addr) for addr in to)
            if cc:
                message['Cc'] = ', '.join(str(addr) for addr in cc)
            if bcc:
                message['Bcc'] = ', '.join(str(addr) for addr in bcc)
            
            # Add custom headers
            if headers:
                for key, value in headers.items():
                    message[key] = value
            
            # Add reply-to header
            if reply_to_id:
                message['In-Reply-To'] = reply_to_id
                message['References'] = reply_to_id
            
            # Encode and return
            return base64.urlsafe_b64encode(
                message.as_bytes()
            ).decode()
        
        # Handle multipart message
        message['Subject'] = subject
        message['To'] = ', '.join(str(addr) for addr in to)
        if cc:
            message['Cc'] = ', '.join(str(addr) for addr in cc)
        if bcc:
            message['Bcc'] = ', '.join(str(addr) for addr in bcc)
        
        # Add text part
        message.attach(MIMEText(body_text, 'plain'))
        
        # Add HTML part
        if body_html:
            message.attach(MIMEText(body_html, 'html'))
        
        # Add attachments
        if attachments:
            for attachment in attachments:
                if attachment.data:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.data)
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename={attachment.filename}'
                    )
                    message.attach(part)
        
        # Add custom headers
        if headers:
            for key, value in headers.items():
                message[key] = value
        
        # Add reply-to header
        if reply_to_id:
            message['In-Reply-To'] = reply_to_id
            message['References'] = reply_to_id
        
        # Encode and return
        return base64.urlsafe_b64encode(
            message.as_bytes()
        ).decode()
    
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
        """Create a draft email."""
        if not self.service:
            raise RuntimeError("Not connected to Gmail API")
        
        # Create message
        message = self._create_message(
            to, subject, body_text, body_html,
            cc, bcc, attachments, reply_to_id
        )
        
        # Create draft
        def create_sync():
            draft = self.service.users().drafts().create(
                userId='me',
                body={'message': {'raw': message}}
            ).execute()
            return draft['id']
        
        return await asyncio.get_event_loop().run_in_executor(
            None, create_sync
        )
    
    async def mark_as_read(self, email_ids: List[str]) -> None:
        """Mark emails as read."""
        await self._modify_labels(email_ids, [], ['UNREAD'])
    
    async def mark_as_unread(self, email_ids: List[str]) -> None:
        """Mark emails as unread."""
        await self._modify_labels(email_ids, ['UNREAD'], [])
    
    async def add_labels(
        self,
        email_ids: List[str],
        labels: List[str]
    ) -> None:
        """Add labels to emails."""
        await self._modify_labels(email_ids, labels, [])
    
    async def remove_labels(
        self,
        email_ids: List[str],
        labels: List[str]
    ) -> None:
        """Remove labels from emails."""
        await self._modify_labels(email_ids, [], labels)
    
    async def _modify_labels(
        self,
        email_ids: List[str],
        add_labels: List[str],
        remove_labels: List[str]
    ) -> None:
        """Modify labels on emails."""
        if not self.service:
            raise RuntimeError("Not connected to Gmail API")
        
        def modify_sync():
            for email_id in email_ids:
                try:
                    self.service.users().messages().modify(
                        userId='me',
                        id=email_id,
                        body={
                            'addLabelIds': add_labels,
                            'removeLabelIds': remove_labels
                        }
                    ).execute()
                except HttpError as e:
                    logger.error(f"Error modifying labels for {email_id}: {e}")
        
        await asyncio.get_event_loop().run_in_executor(
            None, modify_sync
        )
    
    async def delete_emails(self, email_ids: List[str]) -> None:
        """Delete emails (move to trash)."""
        if not self.service:
            raise RuntimeError("Not connected to Gmail API")
        
        def delete_sync():
            for email_id in email_ids:
                try:
                    self.service.users().messages().trash(
                        userId='me',
                        id=email_id
                    ).execute()
                except HttpError as e:
                    logger.error(f"Error deleting email {email_id}: {e}")
        
        await asyncio.get_event_loop().run_in_executor(
            None, delete_sync
        )
    
    async def setup_webhook(self, events: List[str]) -> str:
        """Setup Gmail push notifications."""
        if not self.service:
            raise RuntimeError("Not connected to Gmail API")
        
        def setup_sync():
            # Set up Gmail watch
            request = {
                'labelIds': events if events else ['INBOX'],
                'topicName': self.config.webhook_url  # Should be Pub/Sub topic
            }
            
            result = self.service.users().watch(
                userId='me',
                body=request
            ).execute()
            
            self._watch_id = result['historyId']
            return result['historyId']
        
        return await asyncio.get_event_loop().run_in_executor(
            None, setup_sync
        )
    
    async def stream_emails(
        self,
        filter: Optional[EmailFilter] = None
    ) -> AsyncIterator[Email]:
        """Stream emails in real-time."""
        # Gmail doesn't have true streaming, so we'll poll
        seen_ids = set()
        
        while True:
            try:
                emails = await self.fetch_emails(filter)
                
                for email in emails:
                    if email.id not in seen_ids:
                        seen_ids.add(email.id)
                        yield email
                
                # Wait before next poll
                await asyncio.sleep(self.config.polling_interval)
                
            except Exception as e:
                logger.error(f"Error streaming emails: {e}")
                await asyncio.sleep(self.config.polling_interval) 