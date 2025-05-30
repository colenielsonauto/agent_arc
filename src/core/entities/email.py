"""
Core email entities.

This module re-exports the email entities from the interface layer
for convenience and to maintain a clean separation of concerns.
"""

from ..interfaces.email_provider import (
    Email,
    EmailAddress,
    EmailAttachment,
    EmailFilter,
    EmailProvider,
)

__all__ = [
    "Email",
    "EmailAddress", 
    "EmailAttachment",
    "EmailFilter",
    "EmailProvider",
] 