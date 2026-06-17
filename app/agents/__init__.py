"""
Agents Module

Contains AI agent definitions and configurations.
"""

from .email_agent import create_email_agent, create_email_agent_with_memory
from .email_agent_specialized import create_email_agent as create_specialized_email_agent, get_email_agent_info
from .knowledge_agent import create_knowledge_agent, get_knowledge_agent_info
from .supervisor_agent import create_supervisor_agent, route_query, get_supervisor_info
from .memory_agent import (
    MemoryEnhancedAgent,
    MemoryWorkflow,
    create_memory_agent,
    create_memory_workflow
)

__all__ = [
    # Original agent
    'create_email_agent',
    'create_email_agent_with_memory',
    # Specialized agents
    'create_specialized_email_agent',
    'create_knowledge_agent',
    'create_supervisor_agent',
    # Memory agents
    'MemoryEnhancedAgent',
    'MemoryWorkflow',
    'create_memory_agent',
    'create_memory_workflow',
    # Utilities
    'route_query',
    'get_email_agent_info',
    'get_knowledge_agent_info',
    'get_supervisor_info'
]

# Made with Bob
