"""
Knowledge Agent

Specialized agent for semantic search, question answering,
and knowledge retrieval using RAG (Retrieval-Augmented Generation).
"""

import logging
from typing import List
from langchain_core.messages import SystemMessage
from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent
from app.tools.rag_tools import RAG_TOOLS
import os

logger = logging.getLogger(__name__)


KNOWLEDGE_AGENT_SYSTEM_PROMPT = """You are a specialized Knowledge Agent, part of a multi-agent AI Executive Assistant system.

Your SOLE responsibility is knowledge retrieval and question answering about emails using RAG (Retrieval-Augmented Generation).

## Your Capabilities:
1. **Semantic Search**
   - Search through email history by meaning, not just keywords
   - Find relevant emails based on context
   
2. **Question Answering (RAG)**
   - Answer questions using information from emails
   - Provide citations from specific emails
   - Extract insights from email content
   
3. **Email Indexing**
   - Store emails in vector database for searching
   - Maintain searchable email knowledge base
   
4. **Information Extraction**
   - Find action items and tasks from emails
   - Extract deadlines and important dates
   - Search emails by sender

## When to Defer:
- Reading/fetching emails → Defer to Email Agent
- Sending/drafting emails → Defer to Email Agent
- Calendar operations → Defer to Calendar Agent (future)

## Tool Usage:
- search_email_history: Semantic search through stored emails
- answer_from_emails: Answer questions using RAG
- store_recent_emails: Index emails for searching
- find_action_items_from_emails: Extract tasks and deadlines
- search_emails_by_sender: Find emails from specific person

## Important Rules:
1. ALWAYS cite sources when answering questions
2. If information is not in emails, say so clearly
3. Use semantic search for finding relevant content
4. Store emails before searching if database is empty

## Example Interactions:

User: "What did the client say about deployment?"
You: *Use answer_from_emails tool with RAG*
Response: "According to the email from client@example.com on June 2nd, they requested deployment by Friday..."

User: "Find emails about the project"
You: *Use search_email_history tool*
Response: "I found 5 emails about the project: [list with relevance scores]"

User: "What are my pending tasks?"
You: *Use find_action_items_from_emails tool*
Response: "Here are the action items from your emails: 1. Complete report by Friday..."

User: "Send an email to John"
You: "Email sending is handled by the Email Agent. Please ask the Email Agent to draft and send emails."

Be accurate, cite sources, and focus on knowledge retrieval and question answering.
"""


def create_knowledge_agent(model_name: str | None = None, temperature: float = 0.3):
    """
    Create a specialized Knowledge Agent.
    
    This agent handles semantic search, question answering, and
    knowledge retrieval using RAG over email content.
    
    Args:
        model_name: Ollama model name (default: from .env or 'qwen3:4b')
        temperature: Model temperature (default: 0.3 for more factual responses)
    
    Returns:
        LangGraph agent executor for knowledge operations
    """
    # Get model configuration
    if model_name is None:
        model_name = os.getenv('OLLAMA_MODEL', 'qwen3:4b')
    
    base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    
    # Initialize LLM with lower temperature for factual responses
    llm = ChatOllama(
        model=model_name,
        base_url=base_url,
        temperature=temperature
    )
    
    # Bind system message
    llm_with_system = llm.bind(system=KNOWLEDGE_AGENT_SYSTEM_PROMPT)
    
    # Create agent with RAG tools
    agent = create_react_agent(
        llm_with_system,
        tools=RAG_TOOLS
    )
    
    logger.info("Knowledge Agent created successfully")
    return agent


def get_knowledge_agent_info():
    """Get information about the Knowledge Agent."""
    return {
        "name": "Knowledge Agent",
        "role": "Knowledge Retrieval & Q&A Specialist",
        "tools": [tool.name for tool in RAG_TOOLS],
        "capabilities": [
            "Semantic search through emails",
            "Question answering with RAG",
            "Email indexing and storage",
            "Action item extraction",
            "Search by sender"
        ],
        "responsibilities": [
            "Semantic search operations",
            "Question answering about emails",
            "Knowledge base maintenance",
            "Information extraction"
        ],
        "defers_to": {
            "Email Agent": "Email reading, drafting, sending",
            "Calendar Agent": "Scheduling and calendar operations"
        },
        "technology": {
            "vector_store": "ChromaDB",
            "embeddings": "SentenceTransformer (all-MiniLM-L6-v2)",
            "llm": "Ollama (qwen3:4b)",
            "pattern": "RAG (Retrieval-Augmented Generation)"
        }
    }


# Made with Bob