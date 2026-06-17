"""
Email Agent

AI agent for email management using LangGraph and Ollama.
"""

import os
from typing import List
from langchain_core.messages import SystemMessage
from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent
from app.tools.email_tools import EMAIL_TOOLS
from app.tools.rag_tools import RAG_TOOLS
from app.prompts.email_prompts import EMAIL_AGENT_SYSTEM_MESSAGE

# Combine all tools
ALL_TOOLS = EMAIL_TOOLS + RAG_TOOLS


def create_email_agent(model_name: str | None = None, temperature: float = 0.7):
    """
    Create an email management agent with access to Gmail tools.
    
    The agent can:
    - Fetch recent emails
    - Search for specific emails
    - Summarize email content
    - Answer questions about emails
    
    Args:
        model_name: Ollama model name (default: from .env or 'llama3.2')
        temperature: Model temperature for response generation (default: 0.7)
    
    Returns:
        A LangGraph agent executor that can process email-related queries
    
    Example:
        >>> agent = create_email_agent()
        >>> response = agent.invoke({"messages": [("user", "Show me my recent emails")]})
        >>> print(response["messages"][-1].content)
    """
    
    # Get model name from environment or use default
    if model_name is None:
        model_name = os.getenv('OLLAMA_MODEL', 'llama3.2')
    
    # Get Ollama base URL from environment
    base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    
    # Initialize the LLM with system message
    llm = ChatOllama(
        model=model_name,
        base_url=base_url,
        temperature=temperature
    )
    
    # Bind system message to LLM
    llm_with_system = llm.bind(system=EMAIL_AGENT_SYSTEM_MESSAGE)
    
    # Create the agent with all tools (email + RAG)
    agent = create_react_agent(
        llm_with_system,
        tools=ALL_TOOLS
    )
    
    return agent


def create_email_agent_with_memory(model_name: str | None = None, temperature: float = 0.7):
    """
    Create an email agent with conversation memory.
    
    This version maintains conversation history for context-aware responses.
    
    Args:
        model_name: Ollama model name (default: from .env or 'llama3.2')
        temperature: Model temperature (default: 0.7)
    
    Returns:
        A LangGraph agent executor with memory capabilities
    """
    
    # Get model configuration
    if model_name is None:
        model_name = os.getenv('OLLAMA_MODEL', 'llama3.2')
    
    base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    
    # Initialize LLM with system message
    llm = ChatOllama(
        model=model_name,
        base_url=base_url,
        temperature=temperature
    )
    
    # Bind system message to LLM
    llm_with_system = llm.bind(system=EMAIL_AGENT_SYSTEM_MESSAGE)
    
    # Create agent with memory and all tools
    # The create_react_agent automatically handles message history
    agent = create_react_agent(
        llm_with_system,
        tools=ALL_TOOLS
    )
    
    return agent


# Agent configuration
AGENT_CONFIG = {
    'model': os.getenv('OLLAMA_MODEL', 'llama3.2'),
    'temperature': 0.7,
    'max_iterations': 10,
    'max_execution_time': 60,  # seconds
}


def get_agent_info():
    """
    Get information about the email agent configuration.
    
    Returns:
        dict: Agent configuration details
    """
    return {
        'model': AGENT_CONFIG['model'],
        'temperature': AGENT_CONFIG['temperature'],
        'tools': [tool.name for tool in ALL_TOOLS],
        'capabilities': [
            'Fetch recent emails',
            'Search emails by criteria',
            'Summarize email content',
            'Generate daily digest',
            'Semantic search through email history',
            'Answer questions using RAG',
            'Store emails for searching',
            'Find action items',
            'Search by sender'
        ]
    }

# Made with Bob
