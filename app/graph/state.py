"""
Graph State Definitions

State management for LangGraph workflows including Human-in-the-Loop.
"""

from typing import TypedDict, Annotated, Literal
from langgraph.graph import MessagesState
from langchain_core.messages import BaseMessage
import operator


class EmailDraftState(TypedDict):
    """
    State for email drafting with human approval workflow.
    
    This state tracks the entire lifecycle of an email draft from
    creation through human review to final sending.
    """
    # User's original request
    user_request: str
    
    # Email details
    recipient: str
    subject: str
    body: str
    
    # Draft metadata
    draft_id: str
    is_reply: bool
    original_email_id: str  # For replies
    
    # Human approval
    approved: bool
    feedback: str  # Human feedback if not approved
    
    # Status tracking
    status: Literal["draft", "pending_approval", "approved", "rejected", "sent"]
    error: str  # Error message if any


class ConversationState(MessagesState):
    """
    Extended conversation state with additional context.
    
    Inherits from MessagesState to maintain conversation history
    and adds custom fields for workflow management.
    """
    # Current workflow stage
    current_stage: str
    
    # Pending actions
    pending_action: str
    pending_data: dict
    
    # User preferences
    auto_approve: bool  # Skip approval for certain actions
    
    # Session metadata
    session_id: str
    user_id: str


class MultiAgentState(TypedDict):
    """
    State for multi-agent coordination.
    
    Used by supervisor agent to route tasks to specialized agents.
    """
    # User query
    query: str
    
    # Routing
    next_agent: Literal["email", "knowledge", "calendar", "supervisor"]
    
    # Agent responses
    email_agent_response: str
    knowledge_agent_response: str
    calendar_agent_response: str
    
    # Final output
    final_response: str
    
    # Conversation history
    messages: Annotated[list[BaseMessage], operator.add]


class RAGState(TypedDict):
    """
    State for RAG (Retrieval-Augmented Generation) workflow.
    
    Tracks the retrieve → generate → answer pipeline.
    """
    # Input
    question: str
    
    # Retrieval
    retrieved_emails: list[dict]
    context: str
    
    # Generation
    answer: str
    
    # Metadata
    num_results: int
    search_filters: dict


class WorkflowState(TypedDict):
    """
    Generic workflow state for custom graphs.
    
    Flexible state container for building custom workflows.
    """
    # Input/Output
    input: str
    output: str
    
    # Intermediate results
    intermediate_results: dict
    
    # Control flow
    next_step: str
    should_continue: bool
    
    # Error handling
    error: str
    retry_count: int


# State update helpers

def update_draft_status(
    state: EmailDraftState,
    status: Literal["draft", "pending_approval", "approved", "rejected", "sent"]
) -> EmailDraftState:
    """Update the status of an email draft."""
    state["status"] = status
    return state


def approve_draft(state: EmailDraftState) -> EmailDraftState:
    """Mark a draft as approved."""
    state["approved"] = True
    state["status"] = "approved"
    return state


def reject_draft(state: EmailDraftState, feedback: str) -> EmailDraftState:
    """Mark a draft as rejected with feedback."""
    state["approved"] = False
    state["status"] = "rejected"
    state["feedback"] = feedback
    return state


def mark_draft_sent(state: EmailDraftState) -> EmailDraftState:
    """Mark a draft as successfully sent."""
    state["status"] = "sent"
    return state


# State validators

def validate_email_draft_state(state: EmailDraftState) -> bool:
    """
    Validate that an email draft state has all required fields.
    
    Returns:
        True if valid, False otherwise
    """
    required_fields = ["recipient", "subject", "body"]
    return all(field in state and state[field] for field in required_fields)


def is_draft_ready_to_send(state: EmailDraftState) -> bool:
    """
    Check if a draft is ready to be sent.
    
    Returns:
        True if approved and valid, False otherwise
    """
    return (
        state.get("approved", False) and
        state.get("status") == "approved" and
        validate_email_draft_state(state)
    )


# State initialization helpers

def create_email_draft_state(
    user_request: str,
    recipient: str,
    subject: str,
    body: str,
    is_reply: bool = False,
    original_email_id: str = ""
) -> EmailDraftState:
    """
    Create a new email draft state.
    
    Args:
        user_request: Original user request
        recipient: Email recipient
        subject: Email subject
        body: Email body
        is_reply: Whether this is a reply
        original_email_id: ID of original email if reply
    
    Returns:
        Initialized EmailDraftState
    """
    import uuid
    
    return EmailDraftState(
        user_request=user_request,
        recipient=recipient,
        subject=subject,
        body=body,
        draft_id=str(uuid.uuid4()),
        is_reply=is_reply,
        original_email_id=original_email_id,
        approved=False,
        feedback="",
        status="draft",
        error=""
    )


def create_rag_state(question: str, num_results: int = 3) -> RAGState:
    """
    Create a new RAG state.
    
    Args:
        question: User's question
        num_results: Number of results to retrieve
    
    Returns:
        Initialized RAGState
    """
    return RAGState(
        question=question,
        retrieved_emails=[],
        context="",
        answer="",
        num_results=num_results,
        search_filters={}
    )


# Made with Bob