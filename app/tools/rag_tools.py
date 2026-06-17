"""
RAG Tools Module

LangChain tool wrappers for RAG functionality.
"""

import logging
from typing import Optional, Tuple
from langchain_core.tools import tool
from app.rag.email_store import EmailStore
from app.rag.vector_search import VectorSearch
from app.rag.retriever import EmailRetriever
from app.gmail.email_reader import fetch_recent_emails, get_gmail_service
import os

logger = logging.getLogger(__name__)

# Initialize RAG components (lazy loading)
_email_store = None
_vector_search = None
_retriever = None


def get_rag_components() -> Tuple[Optional[EmailStore], Optional[VectorSearch], Optional[EmailRetriever]]:
    """Get or initialize RAG components."""
    global _email_store, _vector_search, _retriever
    
    if _email_store is None:
        persist_dir = os.getenv('CHROMADB_PATH', './data/chromadb')
        collection_name = os.getenv('CHROMADB_COLLECTION_NAME', 'email_store')
        
        _email_store = EmailStore(
            persist_directory=persist_dir,
            collection_name=collection_name
        )
        _vector_search = VectorSearch(_email_store)
        _retriever = EmailRetriever(_vector_search)
    
    return _email_store, _vector_search, _retriever


@tool
def search_email_history(query: str, max_results: int = 5) -> str:
    """
    Search through email history semantically.
    
    Use this tool to find emails based on content, topics, or keywords.
    It performs semantic search, so you can search by meaning, not just exact words.
    
    Args:
        query: What to search for (e.g., "emails about project deadlines")
        max_results: Maximum number of results to return (default: 5)
    
    Returns:
        Formatted search results with email details
    
    Examples:
        - "Find emails about deployment"
        - "Search for budget discussions"
        - "Emails mentioning client feedback"
    """
    try:
        _, vector_search, _ = get_rag_components()
        
        if vector_search is None:
            return "Error: Vector search system not initialized"
        
        results = vector_search.search(query=query, n_results=max_results)
        
        if not results:
            return f"No emails found matching: {query}"
        
        # Format results
        output = [f"Found {len(results)} emails matching '{query}':\n"]
        
        for i, result in enumerate(results, 1):
            metadata = result.get('metadata', {})
            similarity = result.get('similarity', 0)
            
            output.append(f"\n{i}. Email from {metadata.get('from', 'Unknown')}")
            output.append(f"   Subject: {metadata.get('subject', 'No subject')}")
            output.append(f"   Date: {metadata.get('date', 'Unknown')}")
            output.append(f"   Relevance: {similarity:.0%}")
            
            # Add snippet of content
            doc = result.get('document', '')
            if len(doc) > 200:
                doc = doc[:200] + "..."
            output.append(f"   Preview: {doc}")
        
        return "\n".join(output)
        
    except Exception as e:
        logger.error(f"Error searching email history: {e}")
        return f"Error searching emails: {str(e)}"


@tool
def answer_from_emails(question: str) -> str:
    """
    Answer questions using information from emails (RAG).
    
    This tool retrieves relevant emails and uses them to answer your question.
    It's perfect for questions like "What did X say about Y?" or "When is the deadline?"
    
    Args:
        question: The question to answer based on email content
    
    Returns:
        Answer generated from relevant emails
    
    Examples:
        - "What did the client say about deployment?"
        - "When is the project deadline?"
        - "Who approved the budget?"
    """
    try:
        _, _, retriever = get_rag_components()
        
        if retriever is None:
            return "Error: Email retriever system not initialized"
        
        answer = retriever.answer_question(question=question, n_results=3)
        
        return answer
        
    except Exception as e:
        logger.error(f"Error answering from emails: {e}")
        return f"Error generating answer: {str(e)}"


@tool
def store_recent_emails(max_emails: int = 50) -> str:
    """
    Store recent emails in the vector database for searching.
    
    This tool fetches recent emails from Gmail and stores them with embeddings
    for semantic search. Run this periodically to keep the search index updated.
    
    Args:
        max_emails: Number of recent emails to store (default: 50)
    
    Returns:
        Status message with number of emails stored
    """
    try:
        email_store, _, _ = get_rag_components()
        
        if email_store is None:
            return "Error: Email store system not initialized"
        
        # Fetch recent emails
        emails = fetch_recent_emails(max_results=max_emails)
        
        if not emails:
            return "No emails found to store."
        
        # Prepare emails for storage
        emails_to_store = []
        for email in emails:
            emails_to_store.append({
                'id': email.get('id', ''),
                'subject': email.get('subject', ''),
                'from': email.get('from', ''),
                'to': email.get('to', ''),
                'date': email.get('date', ''),
                'body': email.get('body', ''),
                'thread_id': email.get('threadId', '')
            })
        
        # Store in batch
        results = email_store.store_emails_batch(emails_to_store)
        
        total_stored = email_store.count_emails()
        
        return f"✅ Stored {results['success']} emails (Failed: {results['failed']})\nTotal emails in database: {total_stored}"
        
    except Exception as e:
        logger.error(f"Error storing emails: {e}")
        return f"Error storing emails: {str(e)}"


@tool
def find_action_items_from_emails() -> str:
    """
    Extract action items and tasks from recent emails.
    
    This tool analyzes emails to find tasks, deadlines, and follow-ups
    that require action.
    
    Returns:
        List of action items found in emails
    """
    try:
        _, _, retriever = get_rag_components()
        
        if retriever is None:
            return "Error: Email retriever system not initialized"
        
        action_items = retriever.find_action_items(n_results=10)
        
        return action_items
        
    except Exception as e:
        logger.error(f"Error finding action items: {e}")
        return f"Error extracting action items: {str(e)}"


@tool
def search_emails_by_sender(sender_email: str, max_results: int = 10) -> str:
    """
    Find all emails from a specific sender.
    
    Args:
        sender_email: Email address of the sender
        max_results: Maximum number of results (default: 10)
    
    Returns:
        List of emails from the sender
    """
    try:
        _, vector_search, _ = get_rag_components()
        
        if vector_search is None:
            return "Error: Vector search system not initialized"
        
        results = vector_search.search_by_sender(
            sender=sender_email,
            n_results=max_results
        )
        
        if not results:
            return f"No emails found from: {sender_email}"
        
        output = [f"Found {len(results)} emails from {sender_email}:\n"]
        
        for i, result in enumerate(results, 1):
            metadata = result.get('metadata', {})
            output.append(f"\n{i}. Subject: {metadata.get('subject', 'No subject')}")
            output.append(f"   Date: {metadata.get('date', 'Unknown')}")
        
        return "\n".join(output)
        
    except Exception as e:
        logger.error(f"Error searching by sender: {e}")
        return f"Error searching emails: {str(e)}"


# Export all RAG tools
RAG_TOOLS = [
    search_email_history,
    answer_from_emails,
    store_recent_emails,
    find_action_items_from_emails,
    search_emails_by_sender
]

# Tool descriptions for agent
RAG_TOOLS_DESCRIPTION = """
## RAG (Semantic Search) Tools

5. **search_email_history**: Search through stored emails semantically
   - Use when: User wants to find emails by topic or content
   - Example: "Find emails about the project"

6. **answer_from_emails**: Answer questions using email content (RAG)
   - Use when: User asks questions that can be answered from emails
   - Example: "What did client say about deployment?"

7. **store_recent_emails**: Store recent emails for searching
   - Use when: Need to update the email search index
   - Example: "Index my recent emails"

8. **find_action_items_from_emails**: Extract action items from emails
   - Use when: User wants to see tasks and deadlines
   - Example: "What are my action items?"

9. **search_emails_by_sender**: Find emails from specific sender
   - Use when: User wants emails from a particular person
   - Example: "Show emails from john@example.com"
"""

# Made with Bob
