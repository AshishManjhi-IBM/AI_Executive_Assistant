"""
Specialized Email Agent

Handles all email-related operations including reading, searching,
summarizing, drafting, and sending with HITL approval.
"""

import logging
from typing import List
from langchain_core.messages import SystemMessage
from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent
from app.tools.email_tools import EMAIL_TOOLS
from app.tools.draft_tools import DRAFT_TOOLS
import os

logger = logging.getLogger(__name__)

# Combine email and draft tools
EMAIL_AGENT_TOOLS = EMAIL_TOOLS + DRAFT_TOOLS


EMAIL_AGENT_SYSTEM_PROMPT = """You are a specialized Email Agent, part of a multi-agent AI Executive Assistant system.

Your SOLE responsibility is handling email operations:

## Your Capabilities:
1. **Reading Emails**
   - Fetch recent emails
   - Search for specific emails
   
2. **Email Analysis**
   - Summarize individual emails
   - Generate daily digest reports
   
3. **Email Composition** (with Human-in-the-Loop)
   - Draft new emails
   - Draft replies to existing emails
   - Send emails ONLY after human approval
   
4. **Important Rules**
   - ALWAYS show drafts to users before sending
   - NEVER send emails without explicit approval
   - Use professional tone unless specified otherwise
   - Cite email sources when summarizing

## When to Defer:
- Questions about email content → Defer to Knowledge Agent
- Semantic search through emails → Defer to Knowledge Agent
- Calendar/scheduling → Defer to Calendar Agent (future)

## Tool Usage:
- get_recent_emails: Fetch recent emails from inbox
- search_emails: Search emails by query
- summarize_emails: Summarize email content
- generate_daily_digest: Create categorized email digest
- draft_email: Generate email draft (show to user)
- draft_reply_email: Generate reply draft (show to user)
- send_email_draft: Send ONLY after user approves
- send_reply_draft: Send reply ONLY after user approves

## Example Interactions:

User: "Show me my recent emails"
You: *Use get_recent_emails tool*

User: "Draft an email to john@example.com thanking him for the meeting"
You: *Use draft_email tool, show draft, wait for approval*

User: "What did the client say about deployment?"
You: "This requires semantic search. Please ask the Knowledge Agent."

Be helpful, professional, and ALWAYS prioritize human oversight for sending emails.
"""


def create_email_agent(model_name: str | None = None, temperature: float = 0.7):
    """
    Create a specialized Email Agent.
    
    This agent handles all email operations including reading, searching,
    summarizing, drafting, and sending (with HITL approval).
    
    Args:
        model_name: Ollama model name (default: from .env or 'qwen3:4b')
        temperature: Model temperature (default: 0.7)
    
    Returns:
        LangGraph agent executor for email operations
    """
    # Get model configuration
    if model_name is None:
        model_name = os.getenv('OLLAMA_MODEL', 'qwen3:4b')
    
    base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    
    # Initialize LLM
    llm = ChatOllama(
        model=model_name,
        base_url=base_url,
        temperature=temperature
    )
    
    # Bind system message
    llm_with_system = llm.bind(system=EMAIL_AGENT_SYSTEM_PROMPT)
    
    # Create agent with email tools
    agent = create_react_agent(
        llm_with_system,
        tools=EMAIL_AGENT_TOOLS
    )
    
    logger.info("Email Agent created successfully")
    return agent


def get_email_agent_info():
    """Get information about the Email Agent."""
    return {
        "name": "Email Agent",
        "role": "Email Operations Specialist",
        "tools": [tool.name for tool in EMAIL_AGENT_TOOLS],
        "capabilities": [
            "Fetch and search emails",
            "Summarize email content",
            "Generate daily digests",
            "Draft emails with AI",
            "Send emails with HITL approval"
        ],
        "responsibilities": [
            "All email reading operations",
            "Email composition and drafting",
            "Email sending (with approval)",
            "Email summarization"
        ],
        "defers_to": {
            "Knowledge Agent": "Semantic search, Q&A about emails",
            "Calendar Agent": "Scheduling and calendar operations"
        }
    }


# Made with Bob