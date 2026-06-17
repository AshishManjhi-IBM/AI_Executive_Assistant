"""
Human-in-the-Loop (HITL) Workflow

LangGraph workflow for email drafting with human approval.
"""

import logging
from typing import Literal, cast
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables import RunnableConfig
from app.graph.state import EmailDraftState, create_email_draft_state
from app.graph.nodes import (
    generate_draft_node,
    human_approval_node,
    send_email_node,
    regenerate_draft_node,
    should_send_email
)

logger = logging.getLogger(__name__)


def create_hitl_workflow():
    """
    Create a Human-in-the-Loop workflow for email drafting and approval.
    
    Workflow:
    START → Generate Draft → Human Approval → Send Email → END
                                    ↓
                                Rejected?
                                    ↓
                            Regenerate Draft
    
    Returns:
        Compiled LangGraph workflow with checkpointing
    """
    # Create state graph
    workflow = StateGraph(EmailDraftState)
    
    # Add nodes
    workflow.add_node("generate_draft", generate_draft_node)
    workflow.add_node("human_approval", human_approval_node)
    workflow.add_node("send_email", send_email_node)
    workflow.add_node("regenerate", regenerate_draft_node)
    
    # Set entry point
    workflow.set_entry_point("generate_draft")
    
    # Add edges
    workflow.add_edge("generate_draft", "human_approval")
    
    # Conditional edge from human_approval
    workflow.add_conditional_edges(
        "human_approval",
        should_send_email,
        {
            "send": "send_email",
            "regenerate": "regenerate",
            "wait": END  # Pause for human input
        }
    )
    
    # After regeneration, go back to approval
    workflow.add_edge("regenerate", "human_approval")
    
    # After sending, end workflow
    workflow.add_edge("send_email", END)
    
    # Compile with checkpointing for interrupts
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)
    
    logger.info("HITL workflow created successfully")
    return app


def run_hitl_workflow_interactive(
    user_request: str,
    recipient: str,
    subject: str,
    is_reply: bool = False,
    original_email_id: str = ""
):
    """
    Run the HITL workflow interactively with user approval.
    
    This function demonstrates the full HITL pattern:
    1. Generate draft
    2. Show to user
    3. Get approval/rejection/feedback
    4. Send or regenerate
    
    Args:
        user_request: User's request for the email
        recipient: Email recipient
        subject: Email subject
        is_reply: Whether this is a reply
        original_email_id: ID of original email if reply
    
    Returns:
        Final state after workflow completion
    """
    # Create workflow
    app = create_hitl_workflow()
    
    # Create initial state
    initial_state = create_email_draft_state(
        user_request=user_request,
        recipient=recipient,
        subject=subject,
        body="",  # Will be generated
        is_reply=is_reply,
        original_email_id=original_email_id
    )
    
    # Configuration for checkpointing
    config: RunnableConfig = {"configurable": {"thread_id": "email_draft_1"}}
    
    print("\n" + "="*60)
    print("HITL Email Workflow")
    print("="*60)
    
    # Step 1: Generate draft
    print("\n[1/3] Generating email draft...")
    state = app.invoke(initial_state, config)
    
    # Display draft
    print("\n" + "-"*60)
    print("DRAFT EMAIL:")
    print("-"*60)
    print(f"To: {state['recipient']}")
    print(f"Subject: {state['subject']}")
    print(f"\n{state['body']}")
    print("-"*60)
    
    # Step 2: Get human approval
    while True:
        print("\n[2/3] Review the draft above.")
        print("\nOptions:")
        print("  1. Approve and send")
        print("  2. Reject and provide feedback")
        print("  3. Cancel")
        
        choice = input("\nYour choice (1/2/3): ").strip()
        
        if choice == "1":
            # Approve
            state["approved"] = True
            state["status"] = "approved"
            print("\n[3/3] Sending email...")
            
            # Continue workflow to send
            # Cast state to EmailDraftState to satisfy type checker
            final_state = app.invoke(cast(EmailDraftState, state), config)
            
            if final_state["status"] == "sent":
                print(f"\n✓ Email sent successfully!")
                print(f"Message ID: {final_state['draft_id']}")
            else:
                print(f"\n✗ Error sending email: {final_state.get('error', 'Unknown error')}")
            
            return final_state
            
        elif choice == "2":
            # Reject and get feedback
            feedback = input("\nProvide feedback for improvement: ").strip()
            
            if not feedback:
                print("Feedback cannot be empty. Please try again.")
                continue
            
            state["approved"] = False
            state["status"] = "rejected"
            state["feedback"] = feedback
            
            print("\n[2/3] Regenerating draft based on feedback...")
            
            # Continue workflow to regenerate
            # Cast state to EmailDraftState to satisfy type checker
            state = app.invoke(cast(EmailDraftState, state), config)
            
            # Display new draft
            print("\n" + "-"*60)
            print("UPDATED DRAFT:")
            print("-"*60)
            print(f"To: {state['recipient']}")
            print(f"Subject: {state['subject']}")
            print(f"\n{state['body']}")
            print("-"*60)
            
            # Loop back to approval
            continue
            
        elif choice == "3":
            # Cancel
            print("\n✗ Email draft cancelled.")
            state["status"] = "draft"
            return state
            
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")


def run_hitl_workflow_auto_approve(
    user_request: str,
    recipient: str,
    subject: str,
    is_reply: bool = False,
    original_email_id: str = ""
):
    """
    Run the HITL workflow with automatic approval (for testing).
    
    This bypasses human approval and sends the email immediately.
    Useful for automated testing or when approval is not required.
    
    Args:
        user_request: User's request for the email
        recipient: Email recipient
        subject: Email subject
        is_reply: Whether this is a reply
        original_email_id: ID of original email if reply
    
    Returns:
        Final state after workflow completion
    """
    # Create workflow
    app = create_hitl_workflow()
    
    # Create initial state
    initial_state = create_email_draft_state(
        user_request=user_request,
        recipient=recipient,
        subject=subject,
        body="",
        is_reply=is_reply,
        original_email_id=original_email_id
    )
    
    # Configuration
    config: RunnableConfig = {"configurable": {"thread_id": "email_draft_auto"}}
    
    # Generate draft
    state = app.invoke(initial_state, config)
    
    # Auto-approve
    state["approved"] = True
    state["status"] = "approved"
    
    # Send
    # Cast state to EmailDraftState to satisfy type checker
    final_state = app.invoke(cast(EmailDraftState, state), config)
    
    return final_state


# Workflow information
HITL_WORKFLOW_INFO = {
    "name": "Human-in-the-Loop Email Workflow",
    "description": "Email drafting with human approval before sending",
    "nodes": [
        "generate_draft",
        "human_approval",
        "send_email",
        "regenerate"
    ],
    "features": [
        "AI-generated email drafts",
        "Human review and approval",
        "Feedback-based regeneration",
        "Safe email sending with confirmation"
    ],
    "use_cases": [
        "Drafting important emails",
        "Replying to clients",
        "Sending sensitive information",
        "Automated email composition with oversight"
    ]
}


def get_workflow_info():
    """Get information about the HITL workflow."""
    return HITL_WORKFLOW_INFO


# Made with Bob