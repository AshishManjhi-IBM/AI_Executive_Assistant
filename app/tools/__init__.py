"""
Tools Module

Contains LangGraph tool wrappers for various functionalities.
"""

from .email_tools import get_recent_emails, search_emails, summarize_emails, generate_daily_digest
from .rag_tools import (
    search_email_history,
    answer_from_emails,
    store_recent_emails,
    find_action_items_from_emails,
    search_emails_by_sender,
    RAG_TOOLS
)
from .draft_tools import (
    draft_email,
    draft_reply_email,
    send_email_draft,
    send_reply_draft,
    DRAFT_TOOLS
)

__all__ = [
    # Email tools
    'get_recent_emails',
    'search_emails',
    'summarize_emails',
    'generate_daily_digest',
    # RAG tools
    'search_email_history',
    'answer_from_emails',
    'store_recent_emails',
    'find_action_items_from_emails',
    'search_emails_by_sender',
    'RAG_TOOLS',
    # Draft tools
    'draft_email',
    'draft_reply_email',
    'send_email_draft',
    'send_reply_draft',
    'DRAFT_TOOLS'
]

# Made with Bob
