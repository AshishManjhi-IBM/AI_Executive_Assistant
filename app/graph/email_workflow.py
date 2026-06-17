"""
Email Workflow

LangGraph workflow for email management tasks.
"""

from typing import Dict, Any
from langchain_core.messages import HumanMessage, AIMessage
from app.agents.email_agent import create_email_agent


def create_email_workflow():
    """
    Create a LangGraph workflow for email management.
    
    This workflow uses the ReAct agent pattern which automatically:
    - Receives user input
    - Reasons about what tools to use
    - Executes tools
    - Generates responses
    
    Returns:
        A compiled LangGraph agent executor
    """
    # Create the email agent
    # The create_react_agent already provides a complete workflow
    agent = create_email_agent()
    
    return agent


def run_email_agent(query: str, agent=None) -> str:
    """
    Run the email agent with a single query.
    
    Args:
        query: User's question or request about emails
        agent: Optional pre-created agent (creates new one if None)
    
    Returns:
        str: Agent's response
    
    Example:
        >>> response = run_email_agent("Show me my recent emails")
        >>> print(response)
    """
    if agent is None:
        agent = create_email_workflow()
    
    # Invoke the agent with the query
    result = agent.invoke({
        "messages": [HumanMessage(content=query)]
    })
    
    # Extract the final response
    messages = result.get("messages", [])
    if messages:
        last_message = messages[-1]
        if isinstance(last_message, AIMessage):
            content = last_message.content
            # Handle both string and list content
            if isinstance(content, str):
                return content
            elif isinstance(content, list):
                return str(content)
            return str(content)
        return str(last_message)
    
    return "No response generated"


def run_email_conversation(agent=None) -> None:
    """
    Run an interactive conversation with the email agent.
    
    Args:
        agent: Optional pre-created agent (creates new one if None)
    
    This function provides a REPL-style interface for chatting with the agent.
    Type 'exit', 'quit', or 'q' to end the conversation.
    """
    if agent is None:
        agent = create_email_workflow()
    
    print("\n" + "="*60)
    print("AI Email Assistant - Interactive Mode")
    print("="*60)
    print("\nI can help you with:")
    print("  • Fetching recent emails")
    print("  • Searching for specific emails")
    print("  • Summarizing email content")
    print("  • Answering questions about your emails")
    print("\nType 'exit', 'quit', or 'q' to end the conversation.")
    print("="*60 + "\n")
    
    # Conversation history
    conversation_messages = []
    
    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()
            
            # Check for exit commands
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("\nGoodbye! Have a great day!")
                break
            
            if not user_input:
                continue
            
            # Add user message to history
            conversation_messages.append(HumanMessage(content=user_input))
            
            # Invoke agent with full conversation history
            print("\nAssistant: ", end="", flush=True)
            
            result = agent.invoke({
                "messages": conversation_messages
            })
            
            # Extract and display response
            messages = result.get("messages", [])
            if messages:
                last_message = messages[-1]
                if isinstance(last_message, AIMessage):
                    response = last_message.content
                    print(response)
                    # Update conversation history with full message list
                    conversation_messages = messages
                else:
                    print(str(last_message))
            else:
                print("I couldn't generate a response. Please try again.")
            
            print()  # Empty line for readability
            
        except KeyboardInterrupt:
            print("\n\nConversation interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")
            print("Please try again or type 'exit' to quit.\n")


# Workflow configuration
WORKFLOW_CONFIG = {
    'max_iterations': 10,
    'timeout': 60,  # seconds
    'verbose': False
}


def get_workflow_info() -> Dict[str, Any]:
    """
    Get information about the email workflow.
    
    Returns:
        dict: Workflow configuration and capabilities
    """
    return {
        'type': 'ReAct Agent',
        'pattern': 'Reasoning and Acting',
        'capabilities': [
            'Multi-turn conversations',
            'Tool usage (email fetching and search)',
            'Context-aware responses',
            'Error handling and recovery'
        ],
        'config': WORKFLOW_CONFIG
    }

# Made with Bob
