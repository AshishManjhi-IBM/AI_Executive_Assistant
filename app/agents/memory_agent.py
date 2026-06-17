"""
Memory-Enhanced Agent
Integrates persistent memory with agent workflows
"""

from typing import Dict, Any, List, Optional, TypedDict
from datetime import datetime
import uuid

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from app.memory.memory_store import MemoryStore
from app.memory.checkpointer import get_checkpointer
from app.config.llm_config import create_llm


class SimpleState(TypedDict):
    """Simple state for memory workflow"""
    messages: List[BaseMessage]


class MemoryEnhancedAgent:
    """Agent with persistent memory capabilities"""
    
    def __init__(
        self,
        memory_store: Optional[MemoryStore] = None,
        session_id: Optional[str] = None
    ):
        """Initialize memory-enhanced agent"""
        self.memory_store = memory_store or MemoryStore()
        self.session_id = session_id or str(uuid.uuid4())
        self.llm = create_llm()
        self.checkpointer = get_checkpointer()
    
    def _build_context_from_memory(self) -> str:
        """Build context string from various memory types"""
        context_parts = []
        
        # Get user preferences
        preferences = self.memory_store.get_all_preferences()
        if preferences:
            context_parts.append("User Preferences:")
            for key, value in preferences.items():
                context_parts.append(f"- {key}: {value}")
        
        # Get recent episodic memories (important events)
        episodic = self.memory_store.get_episodic_memories(min_importance=7, limit=5)
        if episodic:
            context_parts.append("\nRecent Important Events:")
            for memory in episodic:
                context_parts.append(f"- {memory['description']} ({memory['timestamp']})")
        
        # Get semantic memories (facts about user)
        user_facts = self.memory_store.get_semantic_memory("user_info")
        if user_facts:
            context_parts.append("\nKnown Facts About User:")
            for key, data in user_facts.items():
                context_parts.append(f"- {key}: {data['value']}")
        
        return "\n".join(context_parts) if context_parts else "No prior context available."
    
    def _get_conversation_history(self, limit: int = 10) -> List[Dict[str, str]]:
        """Get recent conversation history"""
        messages = self.memory_store.get_conversation_history(
            session_id=self.session_id,
            limit=limit
        )
        
        return [
            {"role": msg["role"], "content": msg["content"]}
            for msg in messages
        ]
    
    def _save_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """Save message to conversation history"""
        self.memory_store.add_conversation_message(
            session_id=self.session_id,
            role=role,
            content=content,
            metadata=metadata
        )
    
    def process_message(
        self,
        user_message: str,
        save_to_memory: bool = True
    ) -> str:
        """Process a user message with memory context"""
        
        # Save user message
        if save_to_memory:
            self._save_message("user", user_message)
        
        # Build context from memory
        memory_context = self._build_context_from_memory()
        
        # Get conversation history
        history = self._get_conversation_history()
        
        # Build prompt with context
        system_prompt = f"""You are an AI Executive Assistant with access to the user's history and preferences.

{memory_context}

Use this context to provide personalized and contextually aware responses.
Remember important information from the conversation for future reference."""
        
        # Create messages
        messages: List[BaseMessage] = [SystemMessage(content=system_prompt)]
        
        # Add conversation history
        for msg in history[:-1]:  # Exclude the current message we just added
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))
        
        # Add current message
        messages.append(HumanMessage(content=user_message))
        
        # Get response from LLM
        response = self.llm.invoke(messages)
        response_text = str(response.content) if response.content else ""
        
        # Save assistant response
        if save_to_memory:
            self._save_message("assistant", response_text)
        
        return response_text
    
    def learn_preference(self, key: str, value: Any):
        """Learn and store a user preference"""
        self.memory_store.set_preference(key, value)
        
        # Also add as episodic memory
        self.memory_store.add_episodic_memory(
            event_type="preference_learned",
            description=f"Learned user preference: {key} = {value}",
            importance=6
        )
    
    def remember_fact(
        self,
        category: str,
        key: str,
        value: Any,
        confidence: float = 1.0
    ):
        """Remember a fact about the user or context"""
        self.memory_store.add_semantic_memory(
            category=category,
            key=key,
            value=value,
            confidence=confidence,
            source=f"conversation_{self.session_id}"
        )
    
    def record_event(
        self,
        event_type: str,
        description: str,
        importance: int = 5,
        context: Optional[Dict] = None
    ):
        """Record an important event"""
        self.memory_store.add_episodic_memory(
            event_type=event_type,
            description=description,
            context=context,
            importance=importance
        )
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of current session"""
        messages = self.memory_store.get_conversation_history(self.session_id)
        
        return {
            "session_id": self.session_id,
            "message_count": len(messages),
            "first_message": messages[0]["timestamp"] if messages else None,
            "last_message": messages[-1]["timestamp"] if messages else None,
            "messages": messages
        }
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get overall memory statistics"""
        return self.memory_store.get_memory_stats()
    
    def clear_session(self):
        """Clear current session history"""
        self.memory_store.clear_conversation(self.session_id)
    
    def new_session(self) -> str:
        """Start a new session"""
        self.session_id = str(uuid.uuid4())
        return self.session_id


class MemoryWorkflow:
    """LangGraph workflow with persistent memory"""
    
    def __init__(self, memory_agent: MemoryEnhancedAgent):
        """Initialize workflow with memory agent"""
        self.agent = memory_agent
        self.graph = self._build_graph()
    
    def _build_graph(self):
        """Build the workflow graph"""
        workflow = StateGraph(SimpleState)
        
        # Add nodes
        workflow.add_node("process", self._process_node)
        workflow.add_node("respond", self._respond_node)
        
        # Add edges
        workflow.set_entry_point("process")
        workflow.add_edge("process", "respond")
        workflow.add_edge("respond", END)
        
        # Compile with checkpointer for persistence
        return workflow.compile(checkpointer=self.agent.checkpointer)
    
    def _process_node(self, state: SimpleState) -> SimpleState:
        """Process the input with memory context"""
        user_message = state["messages"][-1].content
        
        # Extract and learn from the message
        # This is where you could add NLP to extract preferences, facts, etc.
        
        return state
    
    def _respond_node(self, state: SimpleState) -> SimpleState:
        """Generate response using memory"""
        user_message = str(state["messages"][-1].content)
        
        # Get response from memory agent
        response = self.agent.process_message(user_message)
        
        # Add to state
        state["messages"].append(AIMessage(content=response))
        
        return state
    
    def invoke(
        self,
        user_message: str,
        thread_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Invoke the workflow with a message"""
        from langchain_core.runnables.config import RunnableConfig
        
        thread_id = thread_id or self.agent.session_id
        
        # Create initial state
        initial_state: SimpleState = {
            "messages": [HumanMessage(content=user_message)]
        }
        
        # Run workflow with thread_id for persistence
        config: RunnableConfig = {"configurable": {"thread_id": thread_id}}
        result = self.graph.invoke(initial_state, config)
        
        return result


def create_memory_agent(
    session_id: Optional[str] = None,
    memory_db_path: str = "data/memory.db"
) -> MemoryEnhancedAgent:
    """Factory function to create a memory-enhanced agent"""
    memory_store = MemoryStore(db_path=memory_db_path)
    return MemoryEnhancedAgent(memory_store=memory_store, session_id=session_id)


def create_memory_workflow(
    session_id: Optional[str] = None
) -> MemoryWorkflow:
    """Factory function to create a memory workflow"""
    agent = create_memory_agent(session_id=session_id)
    return MemoryWorkflow(memory_agent=agent)

# Made with Bob
