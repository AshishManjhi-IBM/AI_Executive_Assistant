"""
Email Draft Tools Module

LangChain tools for drafting and sending emails with LLM assistance.
"""

import logging
from typing import Optional
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from app.gmail.auth import get_gmail_service
from app.gmail.email_sender import send_email, send_reply, format_email_preview, validate_email_address
from app.gmail.email_reader import fetch_recent_emails
import os

logger = logging.getLogger(__name__)

# Initialize LLM for drafting (lazy loading)
_llm = None


def get_llm():
    """Get or initialize LLM for email drafting."""
    global _llm
    if _llm is None:
        model = os.getenv('OLLAMA_MODEL', 'qwen3:4b')
        base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
        _llm = ChatOllama(
            model=model,
            base_url=base_url,
            temperature=0.7
        )
    return _llm


@tool
def draft_email(to: str, subject: str, context: str, tone: str = "professional") -> str:
    """
    Draft an email using AI based on context and requirements.
    
    This tool generates a complete email draft that can be reviewed before sending.
    
    Args:
        to: Recipient email address
        subject: Email subject line
        context: What the email should be about (e.g., "Reply to meeting request", "Follow up on project")
        tone: Desired tone - "professional", "friendly", "formal", "casual" (default: "professional")
    
    Returns:
        Formatted email draft with To, Subject, and Body
    
    Examples:
        - draft_email(to="john@example.com", subject="Meeting Follow-up", context="Thank them for the meeting and confirm next steps")
        - draft_email(to="client@company.com", subject="Project Update", context="Inform about project completion", tone="formal")
    """
    try:
        # Validate email address
        if not validate_email_address(to):
            return f"Error: Invalid email address '{to}'"
        
        # Create drafting prompt
        prompt = f"""You are an AI email assistant. Draft a {tone} email based on the following:

To: {to}
Subject: {subject}
Context: {context}

Requirements:
1. Write a complete, well-structured email
2. Use a {tone} tone
3. Be clear and concise
4. Include appropriate greeting and closing
5. Make it ready to send (no placeholders like [Your Name])

Draft the email body only (no To/Subject headers):"""

        # Generate draft
        llm = get_llm()
        response = llm.invoke(prompt)
        
        # Extract content
        if hasattr(response, 'content'):
            body = response.content
        else:
            body = str(response)
        
        # Ensure body is a string
        if isinstance(body, list):
            body = str(body)
        
        # Format preview
        draft = format_email_preview(to, subject, body)
        
        logger.info(f"Email draft created for {to}")
        return f"EMAIL DRAFT:\n\n{draft}\n\n[This is a draft. Use send_email_draft to send it after review.]"
        
    except Exception as e:
        logger.error(f"Error drafting email: {e}")
        return f"Error drafting email: {str(e)}"


@tool
def draft_reply_email(original_email_id: str, reply_context: str, tone: str = "professional") -> str:
    """
    Draft a reply to an existing email using AI.
    
    This tool fetches the original email and generates an appropriate reply.
    
    Args:
        original_email_id: ID of the email to reply to
        reply_context: What the reply should say (e.g., "Accept the meeting invitation", "Provide project update")
        tone: Desired tone - "professional", "friendly", "formal", "casual" (default: "professional")
    
    Returns:
        Formatted reply draft
    
    Examples:
        - draft_reply_email(original_email_id="abc123", reply_context="Accept the meeting and suggest Tuesday at 2pm")
        - draft_reply_email(original_email_id="xyz789", reply_context="Politely decline due to schedule conflict", tone="friendly")
    """
    try:
        # Get Gmail service
        service = get_gmail_service()
        
        # Fetch original email
        original = service.users().messages().get(
            userId='me',
            id=original_email_id,
            format='full'
        ).execute()
        
        # Extract email details
        headers = original['payload']['headers']
        original_subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '')
        original_from = next((h['value'] for h in headers if h['name'].lower() == 'from'), '')
        
        # Get email body (simplified)
        if 'parts' in original['payload']:
            parts = original['payload']['parts']
            body_data = parts[0]['body'].get('data', '')
        else:
            body_data = original['payload']['body'].get('data', '')
        
        import base64
        if body_data:
            original_body = base64.urlsafe_b64decode(body_data).decode('utf-8', errors='ignore')
        else:
            original_body = "[Original email body not available]"
        
        # Limit original body length for context
        if len(original_body) > 500:
            original_body = original_body[:500] + "..."
        
        # Create reply subject
        reply_subject = original_subject if original_subject.lower().startswith('re:') else f"Re: {original_subject}"
        
        # Create drafting prompt
        prompt = f"""You are an AI email assistant. Draft a {tone} reply to this email:

ORIGINAL EMAIL:
From: {original_from}
Subject: {original_subject}
Body: {original_body}

REPLY CONTEXT: {reply_context}

Requirements:
1. Write a complete, well-structured reply
2. Use a {tone} tone
3. Address the points from the original email
4. Be clear and concise
5. Include appropriate greeting and closing
6. Make it ready to send

Draft the reply body only:"""

        # Generate draft
        llm = get_llm()
        response = llm.invoke(prompt)
        
        # Extract content
        if hasattr(response, 'content'):
            body = response.content
        else:
            body = str(response)
        
        # Ensure body is a string
        if isinstance(body, list):
            body = str(body)
        
        # Format preview
        draft = format_email_preview(original_from, reply_subject, body)
        
        logger.info(f"Reply draft created for email {original_email_id}")
        return f"REPLY DRAFT:\n\n{draft}\n\n[This is a draft. Use send_reply_draft to send it after review.]"
        
    except Exception as e:
        logger.error(f"Error drafting reply: {e}")
        return f"Error drafting reply: {str(e)}"


@tool
def send_email_draft(to: str, subject: str, body: str) -> str:
    """
    Send an email that has been drafted and approved.
    
    IMPORTANT: This actually sends the email. Only use after human approval.
    
    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body content
    
    Returns:
        Confirmation message with sent email ID
    
    Example:
        - send_email_draft(to="john@example.com", subject="Meeting Follow-up", body="Thank you for...")
    """
    try:
        # Validate email
        if not validate_email_address(to):
            return f"Error: Invalid email address '{to}'"
        
        # Get Gmail service
        service = get_gmail_service()
        
        # Send email
        result = send_email(
            service=service,
            to=to,
            subject=subject,
            body=body
        )
        
        message_id = result.get('id', 'unknown')
        logger.info(f"Email sent successfully to {to}. Message ID: {message_id}")
        
        return f"✓ Email sent successfully to {to}\nMessage ID: {message_id}"
        
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return f"Error sending email: {str(e)}"


@tool
def send_reply_draft(original_email_id: str, reply_body: str) -> str:
    """
    Send a reply that has been drafted and approved.
    
    IMPORTANT: This actually sends the reply. Only use after human approval.
    
    Args:
        original_email_id: ID of the email to reply to
        reply_body: Reply message body
    
    Returns:
        Confirmation message with sent reply ID
    
    Example:
        - send_reply_draft(original_email_id="abc123", reply_body="Thank you for your email...")
    """
    try:
        # Get Gmail service
        service = get_gmail_service()
        
        # Send reply
        result = send_reply(
            service=service,
            original_message_id=original_email_id,
            reply_body=reply_body
        )
        
        message_id = result.get('id', 'unknown')
        logger.info(f"Reply sent successfully. Message ID: {message_id}")
        
        return f"✓ Reply sent successfully\nMessage ID: {message_id}"
        
    except Exception as e:
        logger.error(f"Error sending reply: {e}")
        return f"Error sending reply: {str(e)}"


# Export draft tools
DRAFT_TOOLS = [
    draft_email,
    draft_reply_email,
    send_email_draft,
    send_reply_draft
]

# Tool descriptions for agent
DRAFT_TOOLS_DESCRIPTION = """
## Email Drafting Tools

10. **draft_email**: Generate an email draft using AI
    - Use when: User wants to compose a new email
    - Example: "Draft an email to john@example.com about the meeting"

11. **draft_reply_email**: Generate a reply draft to an existing email
    - Use when: User wants to reply to an email
    - Example: "Draft a reply to that email accepting the invitation"

12. **send_email_draft**: Send a drafted email (requires approval)
    - Use when: Draft has been reviewed and approved by user
    - Example: After user confirms "Yes, send it"

13. **send_reply_draft**: Send a drafted reply (requires approval)
    - Use when: Reply draft has been reviewed and approved by user
    - Example: After user confirms "Looks good, send the reply"

IMPORTANT: Always show drafts to the user before sending. Never send emails without explicit approval.
"""

# Made with Bob