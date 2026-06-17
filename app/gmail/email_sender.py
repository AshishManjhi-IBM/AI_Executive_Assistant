"""
Email Sender Module

Handles sending emails via Gmail API.
"""

import logging
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


def create_message(
    to: str,
    subject: str,
    body: str,
    from_email: Optional[str] = None,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None,
    html: bool = False
) -> Dict[str, Any]:
    """
    Create an email message.
    
    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body content
        from_email: Sender email (optional, uses authenticated user if None)
        cc: List of CC recipients (optional)
        bcc: List of BCC recipients (optional)
        html: Whether body is HTML (default: False for plain text)
    
    Returns:
        Dictionary with 'raw' key containing base64 encoded message
    """
    try:
        # Create message container
        if html:
            message = MIMEMultipart('alternative')
            text_part = MIMEText(body, 'plain')
            html_part = MIMEText(body, 'html')
            message.attach(text_part)
            message.attach(html_part)
        else:
            message = MIMEText(body, 'plain')
        
        # Set headers
        message['To'] = to
        message['Subject'] = subject
        
        if from_email:
            message['From'] = from_email
        
        if cc:
            message['Cc'] = ', '.join(cc)
        
        if bcc:
            message['Bcc'] = ', '.join(bcc)
        
        # Encode message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        return {'raw': raw_message}
        
    except Exception as e:
        logger.error(f"Error creating message: {e}")
        raise


def send_message(service, message: Dict[str, Any], user_id: str = 'me') -> Dict[str, Any]:
    """
    Send an email message.
    
    Args:
        service: Authorized Gmail API service instance
        message: Message dictionary with 'raw' key
        user_id: User's email address (default: 'me' for authenticated user)
    
    Returns:
        Sent message details from Gmail API
    """
    try:
        sent_message = service.users().messages().send(
            userId=user_id,
            body=message
        ).execute()
        
        logger.info(f"Message sent successfully. Message ID: {sent_message['id']}")
        return sent_message
        
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        raise


def send_email(
    service,
    to: str,
    subject: str,
    body: str,
    from_email: Optional[str] = None,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None,
    html: bool = False
) -> Dict[str, Any]:
    """
    Create and send an email in one step.
    
    Args:
        service: Authorized Gmail API service instance
        to: Recipient email address
        subject: Email subject
        body: Email body content
        from_email: Sender email (optional)
        cc: List of CC recipients (optional)
        bcc: List of BCC recipients (optional)
        html: Whether body is HTML (default: False)
    
    Returns:
        Sent message details from Gmail API
    
    Example:
        >>> from app.gmail.auth import get_gmail_service
        >>> service = get_gmail_service()
        >>> result = send_email(
        ...     service,
        ...     to="recipient@example.com",
        ...     subject="Test Email",
        ...     body="This is a test email."
        ... )
        >>> print(f"Sent message ID: {result['id']}")
    """
    try:
        # Create message
        message = create_message(
            to=to,
            subject=subject,
            body=body,
            from_email=from_email,
            cc=cc,
            bcc=bcc,
            html=html
        )
        
        # Send message
        result = send_message(service, message)
        
        return result
        
    except Exception as e:
        logger.error(f"Error in send_email: {e}")
        raise


def create_reply_message(
    service,
    original_message_id: str,
    reply_body: str,
    user_id: str = 'me'
) -> Dict[str, Any]:
    """
    Create a reply to an existing email.
    
    Args:
        service: Authorized Gmail API service instance
        original_message_id: ID of the message to reply to
        reply_body: Reply message body
        user_id: User's email address (default: 'me')
    
    Returns:
        Dictionary with 'raw' key containing base64 encoded reply message
    """
    try:
        # Get original message
        original = service.users().messages().get(
            userId=user_id,
            id=original_message_id,
            format='full'
        ).execute()
        
        # Extract headers
        headers = original['payload']['headers']
        subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '')
        to = next((h['value'] for h in headers if h['name'].lower() == 'from'), '')
        
        # Add "Re:" prefix if not already present
        if not subject.lower().startswith('re:'):
            subject = f"Re: {subject}"
        
        # Create reply message
        message = MIMEText(reply_body, 'plain')
        message['To'] = to
        message['Subject'] = subject
        message['In-Reply-To'] = original_message_id
        message['References'] = original_message_id
        
        # Get thread ID
        thread_id = original.get('threadId')
        
        # Encode message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        return {
            'raw': raw_message,
            'threadId': thread_id
        }
        
    except Exception as e:
        logger.error(f"Error creating reply message: {e}")
        raise


def send_reply(
    service,
    original_message_id: str,
    reply_body: str,
    user_id: str = 'me'
) -> Dict[str, Any]:
    """
    Send a reply to an existing email.
    
    Args:
        service: Authorized Gmail API service instance
        original_message_id: ID of the message to reply to
        reply_body: Reply message body
        user_id: User's email address (default: 'me')
    
    Returns:
        Sent reply message details
    
    Example:
        >>> from app.gmail.auth import get_gmail_service
        >>> service = get_gmail_service()
        >>> result = send_reply(
        ...     service,
        ...     original_message_id="abc123",
        ...     reply_body="Thank you for your email."
        ... )
    """
    try:
        # Create reply message
        message = create_reply_message(service, original_message_id, reply_body, user_id)
        
        # Send reply
        result = send_message(service, message, user_id)
        
        logger.info(f"Reply sent successfully to message {original_message_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error sending reply: {e}")
        raise


def validate_email_address(email: str) -> bool:
    """
    Basic email address validation.
    
    Args:
        email: Email address to validate
    
    Returns:
        True if email appears valid, False otherwise
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def format_email_preview(to: str, subject: str, body: str, max_body_length: int = 200) -> str:
    """
    Format an email for preview/display.
    
    Args:
        to: Recipient email
        subject: Email subject
        body: Email body
        max_body_length: Maximum length of body preview (default: 200)
    
    Returns:
        Formatted email preview string
    """
    body_preview = body[:max_body_length]
    if len(body) > max_body_length:
        body_preview += "..."
    
    preview = f"""
To: {to}
Subject: {subject}

{body_preview}
"""
    return preview.strip()

# Made with Bob