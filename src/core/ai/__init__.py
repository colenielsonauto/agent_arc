"""
AI-powered email processing components.

This module contains the core AI functionality for email classification,
response generation, and other intelligent email processing features.
"""

# Import directly from the module to avoid dependency issues
import sys
from pathlib import Path

# Ensure we can import from the current directory
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from ai_classifier import AIEmailClassifier

__all__ = ['AIEmailClassifier'] 