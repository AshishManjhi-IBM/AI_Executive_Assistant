"""
Graph Module

Contains LangGraph workflow definitions and state machines.
"""

from .email_workflow import create_email_workflow, run_email_agent
from .state import EmailDraftState, RAGState, ConversationState, MultiAgentState, create_email_draft_state
from .nodes import (
    generate_draft_node,
    human_approval_node,
    send_email_node,
    regenerate_draft_node,
    retrieve_context_node,
    generate_answer_node
)
from .hitl_workflow import (
    create_hitl_workflow,
    run_hitl_workflow_interactive,
    run_hitl_workflow_auto_approve,
    get_workflow_info
)
from .multi_agent_workflow import (
    create_multi_agent_system,
    run_multi_agent_query,
    run_multi_agent_conversation,
    get_multi_agent_info
)

__all__ = [
    # Email workflow
    'create_email_workflow',
    'run_email_agent',
    # State
    'EmailDraftState',
    'RAGState',
    'ConversationState',
    'MultiAgentState',
    'create_email_draft_state',
    # Nodes
    'generate_draft_node',
    'human_approval_node',
    'send_email_node',
    'regenerate_draft_node',
    'retrieve_context_node',
    'generate_answer_node',
    # HITL Workflow
    'create_hitl_workflow',
    'run_hitl_workflow_interactive',
    'run_hitl_workflow_auto_approve',
    'get_workflow_info',
    # Multi-Agent Workflow
    'create_multi_agent_system',
    'run_multi_agent_query',
    'run_multi_agent_conversation',
    'get_multi_agent_info'
]

# Made with Bob
