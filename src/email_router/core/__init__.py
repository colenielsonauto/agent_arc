"""Core business logic for Email Router."""

from .ingest_email import ingest_email
from .analyze_email import analyze_email
from .forward_and_draft import forward_and_draft

__all__ = ["ingest_email", "analyze_email", "forward_and_draft"]
