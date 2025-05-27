"""
Centralized Gmail API scopes for Email Router MVP.
Import this in all Gmail-related modules to ensure consistency.
"""

GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send", 
    "https://www.googleapis.com/auth/gmail.modify"
] 