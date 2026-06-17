"""
Gmail Integration Module

Provides functionality for Gmail API integration including
authentication and email operations.
"""

from .auth import get_gmail_service, test_authentication
from .email_reader import fetch_recent_emails, format_email_for_display

__all__ = [
    'get_gmail_service',
    'test_authentication',
    'fetch_recent_emails',
    'format_email_for_display'
]

# Made with Bob
