"""
Email Tools for LangGraph

LangGraph tool wrappers for Gmail email operations.
These tools can be used by AI agents to interact with Gmail.
"""

from typing import Optional
from langchain_core.tools import tool
from app.gmail import fetch_recent_emails as _fetch_recent_emails
from app.gmail.email_reader import format_email_for_display


@tool
def get_recent_emails(max_results: int = 5) -> str:
    """
    Fetch recent emails from Gmail inbox.
    
    Use this tool when the user asks about their recent emails, inbox, or wants to see
    what emails they have received.
    
    Args:
        max_results: Number of recent emails to fetch (default: 5, max: 20)
    
    Returns:
        A formatted string containing email details including sender, subject, date, and snippet.
        Returns error message if fetching fails.
    
    Examples:
        - "Show me my recent emails"
        - "What emails did I receive?"
        - "Check my inbox"
    """
    try:
        # Limit max_results to reasonable range
        max_results = min(max(1, max_results), 20)
        
        # Fetch emails
        emails = _fetch_recent_emails(max_results=max_results)
        
        if not emails:
            return "No emails found in your inbox."
        
        # Format emails for LLM consumption
        result = f"Found {len(emails)} recent email(s):\n\n"
        
        for i, email in enumerate(emails, 1):
            result += f"--- Email {i} ---\n"
            result += f"From: {email.get('from', 'Unknown')}\n"
            result += f"Subject: {email.get('subject', 'No Subject')}\n"
            result += f"Date: {email.get('date', 'Unknown')}\n"
            result += f"Preview: {email.get('snippet', 'No preview available')}\n"
            result += "\n"
        
        return result
        
    except FileNotFoundError as e:
        return (
            "Gmail credentials not found. Please set up Gmail API credentials first. "
            "See GMAIL_SETUP.md for instructions."
        )
    except Exception as e:
        return f"Error fetching emails: {str(e)}"


@tool
def search_emails(query: str, max_results: int = 5) -> str:
    """
    Search for emails in Gmail using a search query.
    
    Use this tool when the user wants to find specific emails based on sender, subject,
    keywords, or other criteria.
    
    Args:
        query: Gmail search query (e.g., "from:john@example.com", "subject:meeting", "is:unread")
        max_results: Maximum number of results to return (default: 5, max: 20)
    
    Returns:
        A formatted string containing matching email details.
        Returns error message if search fails.
    
    Examples:
        - "Find emails from john@example.com"
        - "Search for emails about the project"
        - "Show me unread emails"
    
    Gmail search operators:
        - from:sender@example.com - Emails from specific sender
        - to:recipient@example.com - Emails to specific recipient
        - subject:keyword - Emails with keyword in subject
        - is:unread - Unread emails
        - is:starred - Starred emails
        - has:attachment - Emails with attachments
        - after:2024/01/01 - Emails after specific date
        - before:2024/12/31 - Emails before specific date
    """
    try:
        from app.gmail import get_gmail_service
        
        # Limit max_results
        max_results = min(max(1, max_results), 20)
        
        # Get Gmail service
        service = get_gmail_service()
        
        # Search for messages
        results = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=max_results
        ).execute()
        
        messages = results.get('messages', [])
        
        if not messages:
            return f"No emails found matching query: '{query}'"
        
        # Fetch details for each message
        from app.gmail.email_reader import get_email_details
        
        emails = []
        for msg in messages:
            email_data = get_email_details(service, msg['id'])
            if email_data:
                emails.append(email_data)
        
        # Format results
        result = f"Found {len(emails)} email(s) matching '{query}':\n\n"
        
        for i, email in enumerate(emails, 1):
            result += f"--- Email {i} ---\n"
            result += f"From: {email.get('from', 'Unknown')}\n"
            result += f"Subject: {email.get('subject', 'No Subject')}\n"
            result += f"Date: {email.get('date', 'Unknown')}\n"
            result += f"Preview: {email.get('snippet', 'No preview available')}\n"
            result += "\n"
        
        return result
        
    except FileNotFoundError:
        return (
            "Gmail credentials not found. Please set up Gmail API credentials first. "
            "See GMAIL_SETUP.md for instructions."
        )
    except Exception as e:
        return f"Error searching emails: {str(e)}"



@tool
def summarize_emails(max_results: int = 10) -> str:
    """
    Fetch recent emails and generate an AI-powered summary.
    
    Use this tool when the user wants a summary or overview of their emails,
    rather than seeing individual email details.
    
    Args:
        max_results: Number of recent emails to summarize (default: 10, max: 20)
    
    Returns:
        An AI-generated summary of the emails including:
        - Total number of emails
        - Key senders and topics
        - Important or urgent messages
        - Action items or follow-ups needed
    
    Examples:
        - "Summarize my emails"
        - "Give me an overview of my inbox"
        - "What are the main topics in my recent emails?"
    """
    try:
        import os
        from langchain_ollama import ChatOllama
        
        # Limit max_results
        max_results = min(max(1, max_results), 20)
        
        # Fetch emails
        emails = _fetch_recent_emails(max_results=max_results)
        
        if not emails:
            return "No emails found to summarize."
        
        # Prepare email data for summarization
        email_text = f"Summarize these {len(emails)} emails:\n\n"
        
        for i, email in enumerate(emails, 1):
            email_text += f"Email {i}:\n"
            email_text += f"From: {email.get('from', 'Unknown')}\n"
            email_text += f"Subject: {email.get('subject', 'No Subject')}\n"
            email_text += f"Date: {email.get('date', 'Unknown')}\n"
            email_text += f"Preview: {email.get('snippet', 'No preview')}\n\n"
        
        # Initialize LLM for summarization
        model_name = os.getenv('OLLAMA_MODEL', 'qwen3:4b')
        base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
        
        llm = ChatOllama(
            model=model_name,
            base_url=base_url,
            temperature=0.3  # Lower temperature for more focused summaries
        )
        
        # Create summarization prompt
        summary_prompt = f"""You are an email assistant. Analyze these emails and provide a concise summary.

{email_text}

Please provide:
1. Total number of emails analyzed
2. Main senders (top 3-5)
3. Key topics or themes
4. Any urgent or important messages
5. Suggested action items or follow-ups

Keep the summary clear, concise, and actionable."""

        # Generate summary
        response = llm.invoke(summary_prompt)
        
        # Extract content from response
        if hasattr(response, 'content'):
            content = response.content
            # Handle both string and list content
            if isinstance(content, str):
                summary = content
            elif isinstance(content, list):
                summary = str(content)
            else:
                summary = str(content)
        else:
            summary = str(response)
        
        return summary
        
    except FileNotFoundError:
        return (
            "Gmail credentials not found. Please set up Gmail API credentials first. "
            "See GMAIL_SETUP.md for instructions."
        )
    except Exception as e:
        return f"Error summarizing emails: {str(e)}"

# Tool metadata for agent discovery
EMAIL_TOOLS = [get_recent_emails, search_emails, summarize_emails]

EMAIL_TOOLS_DESCRIPTION = """
Available Email Tools:

1. get_recent_emails(max_results: int = 5)
   - Fetches recent emails from inbox
   - Use when user asks about recent emails or inbox

2. search_emails(query: str, max_results: int = 5)
   - Searches emails using Gmail search syntax
   - Use when user wants to find specific emails
   - Supports Gmail search operators (from:, subject:, is:unread, etc.)

3. summarize_emails(max_results: int = 10)
   - Generates AI-powered summary of recent emails
   - Use when user wants an overview or summary of their inbox
   - Provides key senders, topics, urgent messages, and action items
"""

# Made with Bob


@tool
def generate_daily_digest(max_emails: int = 100) -> str:
    """
    Generate a comprehensive daily email digest using Map-Reduce approach.
    
    This tool processes large volumes of emails (up to 100+) by:
    1. MAP: Summarizing emails in batches
    2. REDUCE: Combining summaries into a structured daily report
    
    Use this tool when the user wants:
    - A daily digest or daily summary
    - Overview of many emails (50-100+)
    - Structured report with categories
    
    Args:
        max_emails: Maximum number of emails to process (default: 100)
    
    Returns:
        A structured daily digest with categories:
        - Urgent items
        - Meetings and calendar
        - Finance and billing
        - Personal messages
        - Other updates
    
    Examples:
        - "Generate my daily email digest"
        - "Give me today's email summary"
        - "What happened in my inbox today?"
    """
    try:
        import os
        from langchain_ollama import ChatOllama
        from datetime import datetime
        
        # Limit max_emails to reasonable range
        max_emails = min(max(10, max_emails), 200)
        
        # Fetch emails
        emails = _fetch_recent_emails(max_results=max_emails)
        
        if not emails:
            return "No emails found to generate digest."
        
        # Initialize LLM
        model_name = os.getenv('OLLAMA_MODEL', 'qwen3:4b')
        base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
        
        llm = ChatOllama(
            model=model_name,
            base_url=base_url,
            temperature=0.3
        )
        
        # MAP PHASE: Process emails in batches
        batch_size = 15  # Process 15 emails at a time
        batch_summaries = []
        
        for i in range(0, len(emails), batch_size):
            batch = emails[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            
            # Format batch for summarization
            batch_text = f"Batch {batch_num} ({len(batch)} emails):\n\n"
            for j, email in enumerate(batch, 1):
                batch_text += f"Email {j}:\n"
                batch_text += f"From: {email.get('from', 'Unknown')}\n"
                batch_text += f"Subject: {email.get('subject', 'No Subject')}\n"
                batch_text += f"Date: {email.get('date', 'Unknown')}\n"
                batch_text += f"Preview: {email.get('snippet', 'No preview')}\n\n"
            
            # Summarize batch with categorization
            map_prompt = f"""Analyze these emails and categorize them:

{batch_text}

Categorize each email into ONE of these categories:
- URGENT: Time-sensitive, requires immediate action
- MEETINGS: Meeting invites, calendar events, scheduling
- FINANCE: Bills, invoices, payments, financial matters
- PERSONAL: Personal messages, social updates
- WORK: Work-related updates, projects, tasks
- OTHER: Everything else

For each category, list:
- Email subject
- Sender
- Brief note

Format:
URGENT:
- [Subject] from [Sender]: [Note]

MEETINGS:
- [Subject] from [Sender]: [Note]

(etc.)"""

            # Get batch summary
            response = llm.invoke(map_prompt)
            
            # Extract content
            if hasattr(response, 'content'):
                content = response.content
                if isinstance(content, str):
                    batch_summary = content
                else:
                    batch_summary = str(content)
            else:
                batch_summary = str(response)
            
            batch_summaries.append(batch_summary)
        
        # REDUCE PHASE: Combine all batch summaries into final digest
        combined_summaries = "\n\n---\n\n".join(batch_summaries)
        
        reduce_prompt = f"""You are creating a Daily Email Digest. Combine these batch summaries into ONE comprehensive report.

{combined_summaries}

Create a professional daily digest with this EXACT format:

📧 DAILY EMAIL DIGEST
Date: {datetime.now().strftime('%B %d, %Y')}
Total Emails Analyzed: {len(emails)}

🚨 URGENT ITEMS
[List urgent items with sender and brief description]
[If none, write "None"]

📅 MEETINGS & CALENDAR
[List meeting invites and calendar events]
[If none, write "None"]

💰 FINANCE & BILLING
[List bills, invoices, financial matters]
[If none, write "None"]

💼 WORK UPDATES
[List work-related emails, projects, tasks]
[If none, write "None"]

👤 PERSONAL
[List personal messages]
[If none, write "None"]

📬 OTHER UPDATES
[List other emails]
[If none, write "None"]

✅ ACTION ITEMS
[List specific actions needed]

Keep it concise and actionable. Focus on what matters most."""

        # Generate final digest
        final_response = llm.invoke(reduce_prompt)
        
        # Extract final digest
        if hasattr(final_response, 'content'):
            content = final_response.content
            if isinstance(content, str):
                digest = content
            else:
                digest = str(content)
        else:
            digest = str(final_response)
        
        return digest
        
    except FileNotFoundError:
        return (
            "Gmail credentials not found. Please set up Gmail API credentials first. "
            "See GMAIL_SETUP.md for instructions."
        )
    except Exception as e:
        return f"Error generating daily digest: {str(e)}"


# Tool metadata for agent discovery
EMAIL_TOOLS = [get_recent_emails, search_emails, summarize_emails, generate_daily_digest]

EMAIL_TOOLS_DESCRIPTION = """
Available Email Tools:

1. get_recent_emails(max_results: int = 5)
   - Fetches recent emails from inbox
   - Use when user asks about recent emails or inbox

2. search_emails(query: str, max_results: int = 5)
   - Searches emails using Gmail search syntax
   - Use when user wants to find specific emails
   - Supports Gmail search operators (from:, subject:, is:unread, etc.)

3. summarize_emails(max_results: int = 10)
   - Generates AI-powered summary of recent emails
   - Use when user wants an overview or summary of their inbox
   - Provides key senders, topics, urgent messages, and action items

4. generate_daily_digest(max_emails: int = 100)
   - Generates comprehensive daily email digest using Map-Reduce
   - Handles 100+ emails efficiently
   - Categorizes into: Urgent, Meetings, Finance, Work, Personal, Other
   - Use for daily summaries or large volume email analysis
   - Provides structured report with action items
"""
