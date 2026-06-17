"""
Graph Nodes

Node functions for LangGraph workflows including Human-in-the-Loop.
"""

import logging
from typing import Dict, Any
from langchain_ollama import ChatOllama
from app.graph.state import EmailDraftState, RAGState, create_email_draft_state
from app.gmail.email_sender import send_email, send_reply, format_email_preview
from app.gmail.auth import get_gmail_service
from app.rag.email_store import EmailStore
from app.rag.vector_search import VectorSearch
from app.rag.retriever import EmailRetriever
import os

logger = logging.getLogger(__name__)

# Initialize LLM (lazy loading)
_llm = None


def get_llm():
    """Get or initialize LLM."""
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


# ============================================================================
# Email Draft Nodes (HITL Workflow)
# ============================================================================

def generate_draft_node(state: EmailDraftState) -> EmailDraftState:
    """
    Generate an email draft based on user request.
    
    This is the first node in the HITL workflow.
    """
    try:
        logger.info("Generating email draft...")
        
        user_request = state.get("user_request", "")
        recipient = state.get("recipient", "")
        subject = state.get("subject", "")
        
        # Create prompt for draft generation
        prompt = f"""You are an AI email assistant. Generate a professional email based on:

User Request: {user_request}
To: {recipient}
Subject: {subject}

Write a complete, well-structured email body. Be professional, clear, and concise.
Include appropriate greeting and closing.

Email body:"""

        # Generate draft
        llm = get_llm()
        response = llm.invoke(prompt)
        
        # Extract content
        if hasattr(response, 'content'):
            body = response.content
        else:
            body = str(response)
        
        # Ensure body is string
        if isinstance(body, list):
            body = str(body)
        
        # Update state
        state["body"] = body
        state["status"] = "pending_approval"
        
        logger.info("Draft generated successfully")
        return state
        
    except Exception as e:
        logger.error(f"Error generating draft: {e}")
        state["error"] = str(e)
        state["status"] = "draft"
        return state


def human_approval_node(state: EmailDraftState) -> EmailDraftState:
    """
    Wait for human approval of the draft.
    
    This node presents the draft to the user and waits for approval.
    In a real implementation, this would use an interrupt to pause execution.
    """
    try:
        logger.info("Waiting for human approval...")
        
        # Format draft for display
        recipient = state.get("recipient", "")
        subject = state.get("subject", "")
        body = state.get("body", "")
        
        draft_preview = format_email_preview(recipient, subject, body)
        
        # In a real HITL implementation, this would:
        # 1. Display the draft to the user
        # 2. Use graph.interrupt() to pause execution
        # 3. Wait for user input (approve/reject/modify)
        # 4. Resume execution with updated state
        
        # For now, we'll mark it as pending approval
        # The actual approval will be handled by the workflow runner
        state["status"] = "pending_approval"
        
        logger.info("Draft ready for approval")
        return state
        
    except Exception as e:
        logger.error(f"Error in approval node: {e}")
        state["error"] = str(e)
        return state


def send_email_node(state: EmailDraftState) -> EmailDraftState:
    """
    Send the approved email.
    
    This node only executes if the draft has been approved.
    """
    try:
        logger.info("Sending email...")
        
        # Check if approved
        if not state.get("approved", False):
            logger.warning("Attempted to send unapproved email")
            state["error"] = "Email not approved"
            return state
        
        # Get email details
        recipient = state.get("recipient", "")
        subject = state.get("subject", "")
        body = state.get("body", "")
        is_reply = state.get("is_reply", False)
        original_email_id = state.get("original_email_id", "")
        
        # Get Gmail service
        service = get_gmail_service()
        
        # Send email or reply
        if is_reply and original_email_id:
            result = send_reply(
                service=service,
                original_message_id=original_email_id,
                reply_body=body
            )
        else:
            result = send_email(
                service=service,
                to=recipient,
                subject=subject,
                body=body
            )
        
        # Update state
        state["status"] = "sent"
        state["draft_id"] = result.get("id", "")
        
        logger.info(f"Email sent successfully. ID: {state['draft_id']}")
        return state
        
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        state["error"] = str(e)
        state["status"] = "approved"  # Keep as approved so user can retry
        return state


def regenerate_draft_node(state: EmailDraftState) -> EmailDraftState:
    """
    Regenerate draft based on human feedback.
    
    This node is called when the user rejects the draft and provides feedback.
    """
    try:
        logger.info("Regenerating draft based on feedback...")
        
        user_request = state.get("user_request", "")
        recipient = state.get("recipient", "")
        subject = state.get("subject", "")
        feedback = state.get("feedback", "")
        previous_body = state.get("body", "")
        
        # Create prompt with feedback
        prompt = f"""You are an AI email assistant. Regenerate an email based on:

Original Request: {user_request}
To: {recipient}
Subject: {subject}

Previous Draft:
{previous_body}

User Feedback: {feedback}

Incorporate the feedback and write an improved email body.
Be professional, clear, and concise.

Improved email body:"""

        # Generate new draft
        llm = get_llm()
        response = llm.invoke(prompt)
        
        # Extract content
        if hasattr(response, 'content'):
            body = response.content
        else:
            body = str(response)
        
        # Ensure body is string
        if isinstance(body, list):
            body = str(body)
        
        # Update state
        state["body"] = body
        state["status"] = "pending_approval"
        state["feedback"] = ""  # Clear feedback
        
        logger.info("Draft regenerated successfully")
        return state
        
    except Exception as e:
        logger.error(f"Error regenerating draft: {e}")
        state["error"] = str(e)
        return state


# ============================================================================
# RAG Workflow Nodes
# ============================================================================

def retrieve_context_node(state: RAGState) -> RAGState:
    """
    Retrieve relevant emails for a question.
    
    This is the first node in the RAG workflow.
    """
    try:
        logger.info("Retrieving context...")
        
        question = state.get("question", "")
        num_results = state.get("num_results", 3)
        search_filters = state.get("search_filters", {})
        
        # Initialize RAG components
        email_store = EmailStore()
        vector_search = VectorSearch(email_store)
        
        # Search for relevant emails
        results = vector_search.search(
            query=question,
            n_results=num_results,
            **search_filters
        )
        
        # Update state
        state["retrieved_emails"] = results
        
        # Format context
        context_parts = []
        for i, email in enumerate(results, 1):
            metadata = email.get('metadata', {})
            document = email.get('document', '')
            context_parts.append(f"Email {i}:")
            context_parts.append(f"From: {metadata.get('from', 'Unknown')}")
            context_parts.append(f"Subject: {metadata.get('subject', 'No subject')}")
            context_parts.append(f"Content: {document}\n")
        
        state["context"] = "\n".join(context_parts)
        
        logger.info(f"Retrieved {len(results)} emails")
        return state
        
    except Exception as e:
        logger.error(f"Error retrieving context: {e}")
        state["context"] = ""
        return state


def generate_answer_node(state: RAGState) -> RAGState:
    """
    Generate an answer based on retrieved context.
    
    This is the second node in the RAG workflow.
    """
    try:
        logger.info("Generating answer...")
        
        question = state.get("question", "")
        context = state.get("context", "")
        
        if not context:
            state["answer"] = "I couldn't find any relevant emails to answer your question."
            return state
        
        # Create RAG prompt
        prompt = f"""You are an AI assistant analyzing email content.

Context from emails:
{context}

Question: {question}

Instructions:
1. Answer based ONLY on the provided email context
2. Cite specific emails when providing information
3. If the information is not in the emails, say so
4. Be concise and accurate

Answer:"""

        # Generate answer
        llm = get_llm()
        response = llm.invoke(prompt)
        
        # Extract content
        if hasattr(response, 'content'):
            answer = response.content
        else:
            answer = str(response)
        
        # Ensure answer is string
        if isinstance(answer, list):
            answer = str(answer)
        
        state["answer"] = answer
        
        logger.info("Answer generated successfully")
        return state
        
    except Exception as e:
        logger.error(f"Error generating answer: {e}")
        state["answer"] = f"Error generating answer: {str(e)}"
        return state


# ============================================================================
# Conditional Edge Functions
# ============================================================================

def should_send_email(state: EmailDraftState) -> str:
    """
    Determine if email should be sent or regenerated.
    
    Returns:
        "send" if approved, "regenerate" if rejected, "wait" if pending
    """
    status = state.get("status", "")
    approved = state.get("approved", False)
    
    if status == "approved" and approved:
        return "send"
    elif status == "rejected":
        return "regenerate"
    else:
        return "wait"


def check_approval_status(state: EmailDraftState) -> bool:
    """
    Check if draft has been approved.
    
    Returns:
        True if approved, False otherwise
    """
    return state.get("approved", False) and state.get("status") == "approved"


# Made with Bob