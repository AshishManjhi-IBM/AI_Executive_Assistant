"""
Gmail Authentication Module

Handles OAuth2 authentication for Gmail API access.
"""

import os
import pickle
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Token file path
TOKEN_FILE = 'token.pickle'
CREDENTIALS_FILE = 'credentials.json'


def get_gmail_service():
    """
    Authenticate and return Gmail API service instance.
    
    Returns:
        googleapiclient.discovery.Resource: Gmail API service
        
    Raises:
        FileNotFoundError: If credentials.json is not found
        Exception: If authentication fails
    """
    creds = None
    
    # Check if token file exists
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)
    
    # If no valid credentials, authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # Refresh expired token
            creds.refresh(Request())
        else:
            # Check if credentials file exists
            if not os.path.exists(CREDENTIALS_FILE):
                raise FileNotFoundError(
                    f"\n{CREDENTIALS_FILE} not found!\n\n"
                    "Please follow these steps:\n"
                    "1. Go to https://console.cloud.google.com/\n"
                    "2. Create a new project or select existing\n"
                    "3. Enable Gmail API\n"
                    "4. Create OAuth 2.0 credentials (Desktop app)\n"
                    "5. Download credentials and save as 'credentials.json'\n"
                    "6. Place credentials.json in the project root directory\n"
                )
            
            # Perform OAuth flow
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES
            )
            creds = flow.run_local_server(port=0)
        
        # Save credentials for future use
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)
    
    # Build and return Gmail service
    service = build('gmail', 'v1', credentials=creds)
    return service


def test_authentication():
    """
    Test Gmail authentication and return user profile.
    
    Returns:
        dict: User profile information
    """
    try:
        service = get_gmail_service()
        profile = service.users().getProfile(userId='me').execute()
        return {
            'email': profile.get('emailAddress'),
            'messages_total': profile.get('messagesTotal'),
            'threads_total': profile.get('threadsTotal'),
            'status': 'authenticated'
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }

# Made with Bob
