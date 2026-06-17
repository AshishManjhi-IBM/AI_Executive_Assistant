"""
Gmail Email Reader Module

Provides functionality to fetch and parse emails from Gmail.
"""

import base64
from typing import List, Dict, Optional
from email.mime.text import MIMEText
from .auth import get_gmail_service


def fetch_recent_emails(max_results: int = 10) -> List[Dict]:
    """
    Fetch recent emails from Gmail inbox.
    
    Args:
        max_results (int): Maximum number of emails to fetch (default: 10)
        
    Returns:
        List[Dict]: List of email dictionaries containing:
            - id: Email ID
            - thread_id: Thread ID
            - from: Sender email
            - to: Recipient email
            - subject: Email subject
            - snippet: Email preview text
            - date: Email date
            - body: Email body (if available)
            
    Raises:
        Exception: If Gmail API call fails
    """
    try:
        # Get Gmail service
        service = get_gmail_service()
        
        # Fetch message list
        results = service.users().messages().list(
            userId='me',
            maxResults=max_results,
            labelIds=['INBOX']
        ).execute()
        
        messages = results.get('messages', [])
        
        if not messages:
            print("No messages found in inbox.")
            return []
        
        # Fetch full details for each message
        emails = []
        for msg in messages:
            email_data = get_email_details(service, msg['id'])
            if email_data:
                emails.append(email_data)
        
        return emails
        
    except Exception as e:
        print(f"Error fetching emails: {e}")
        raise


def get_email_details(service, msg_id: str) -> Optional[Dict]:
    """
    Get detailed information for a specific email.
    
    Args:
        service: Gmail API service instance
        msg_id (str): Email message ID
        
    Returns:
        Dict: Email details or None if error
    """
    try:
        # Get message details
        message = service.users().messages().get(
            userId='me',
            id=msg_id,
            format='full'
        ).execute()
        
        # Extract headers
        headers = message['payload']['headers']
        subject = get_header_value(headers, 'Subject')
        from_email = get_header_value(headers, 'From')
        to_email = get_header_value(headers, 'To')
        date = get_header_value(headers, 'Date')
        
        # Extract body
        body = get_email_body(message['payload'])
        
        # Build email data
        email_data = {
            'id': message['id'],
            'thread_id': message['threadId'],
            'from': from_email,
            'to': to_email,
            'subject': subject,
            'date': date,
            'snippet': message.get('snippet', ''),
            'body': body,
            'labels': message.get('labelIds', [])
        }
        
        return email_data
        
    except Exception as e:
        print(f"Error getting email details for {msg_id}: {e}")
        return None


def get_header_value(headers: List[Dict], name: str) -> str:
    """
    Extract header value by name.
    
    Args:
        headers (List[Dict]): List of email headers
        name (str): Header name to find
        
    Returns:
        str: Header value or empty string if not found
    """
    for header in headers:
        if header['name'].lower() == name.lower():
            return header['value']
    return ''


def get_email_body(payload: Dict) -> str:
    """
    Extract email body from payload.
    
    Args:
        payload (Dict): Email payload
        
    Returns:
        str: Email body text
    """
    body = ''
    
    # Check if body is in the main payload
    if 'body' in payload and 'data' in payload['body']:
        body = base64.urlsafe_b64decode(
            payload['body']['data']
        ).decode('utf-8')
        return body
    
    # Check parts for multipart messages
    if 'parts' in payload:
        for part in payload['parts']:
            # Look for text/plain or text/html
            if part['mimeType'] == 'text/plain':
                if 'data' in part['body']:
                    body = base64.urlsafe_b64decode(
                        part['body']['data']
                    ).decode('utf-8')
                    return body
            elif part['mimeType'] == 'text/html' and not body:
                if 'data' in part['body']:
                    body = base64.urlsafe_b64decode(
                        part['body']['data']
                    ).decode('utf-8')
            
            # Recursively check nested parts
            if 'parts' in part:
                nested_body = get_email_body(part)
                if nested_body:
                    return nested_body
    
    return body


def format_email_for_display(email: Dict) -> str:
    """
    Format email data for console display.
    
    Args:
        email (Dict): Email data dictionary
        
    Returns:
        str: Formatted email string
    """
    separator = "=" * 80
    
    formatted = f"\n{separator}\n"
    formatted += f"From: {email.get('from', 'N/A')}\n"
    formatted += f"To: {email.get('to', 'N/A')}\n"
    formatted += f"Date: {email.get('date', 'N/A')}\n"
    formatted += f"Subject: {email.get('subject', 'N/A')}\n"
    formatted += f"{separator}\n"
    formatted += f"Snippet: {email.get('snippet', 'N/A')}\n"
    formatted += f"{separator}\n"
    
    # Optionally include body (truncated)
    body = email.get('body', '')
    if body:
        # Truncate long bodies
        max_body_length = 500
        if len(body) > max_body_length:
            body = body[:max_body_length] + "...\n[Body truncated]"
        formatted += f"Body:\n{body}\n"
        formatted += f"{separator}\n"
    
    return formatted

# Made with Bob
