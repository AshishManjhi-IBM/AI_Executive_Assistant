"""
AI Executive Assistant - Streamlit Web Interface

This is the main Streamlit application that provides a conversational
interface for the AI Executive Assistant.
"""

import streamlit as st
import os
import sys
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="AI Executive Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
    }
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables"""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'system_initialized' not in st.session_state:
        st.session_state.system_initialized = False


def display_sidebar():
    """Display sidebar with configuration and options"""
    with st.sidebar:
        st.title("⚙️ Configuration")
        
        # System Status
        st.subheader("System Status")
        
        # Check Ollama configuration
        ollama_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
        ollama_model = os.getenv('OLLAMA_MODEL', 'llama3.2')
        
        st.info(f"**Ollama URL:** {ollama_url}")
        st.info(f"**Model:** {ollama_model}")
        
        # ChromaDB status
        chromadb_path = os.getenv('CHROMADB_PATH', './data/chromadb')
        if Path(chromadb_path).exists():
            st.success("✓ ChromaDB: Connected")
        else:
            st.warning("⚠ ChromaDB: Not initialized")
        
        st.divider()
        
        # Features
        st.subheader("🎯 Features")
        st.markdown("""
        - 📧 Email Management
        - 📅 Calendar Integration
        - 📝 Task Management
        - 🔍 Research & Search
        - 💬 Conversational AI
        - 🧠 Context Memory
        """)
        
        st.divider()
        
        # Actions
        st.subheader("Actions")
        if st.button("🔄 Clear Chat History"):
            st.session_state.messages = []
            st.rerun()
        
        if st.button("📊 View System Info"):
            st.session_state.show_system_info = True


def display_welcome_message():
    """Display welcome message for new users"""
    st.markdown('<div class="main-header">🤖 AI Executive Assistant</div>', unsafe_allow_html=True)
    
    st.markdown("""
    ### Welcome! I'm your AI Executive Assistant.
    
    I can help you with:
    - 📧 Managing your emails
    - 📅 Scheduling and calendar management
    - 📝 Task organization and prioritization
    - 🔍 Research and information gathering
    - 💡 Answering questions and providing insights
    
    **To get started:**
    1. Make sure Ollama is running (`ollama serve`)
    2. Ensure you have pulled a model (`ollama pull llama3.2`)
    3. Type your message below!
    
    ---
    """)


def display_chat_interface():
    """Display the main chat interface"""
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("How can I assist you today?"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate assistant response (placeholder for now)
        with st.chat_message("assistant"):
            response = generate_response(prompt)
            st.markdown(response)
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})


def generate_response(prompt: str) -> str:
    """
    Generate response to user prompt
    
    NOTE: This is a placeholder implementation.
    In the full implementation, this will:
    1. Use LangGraph to orchestrate agents
    2. Call appropriate tools based on the request
    3. Use RAG for context-aware responses
    4. Maintain conversation memory
    """
    
    # Placeholder response
    response = f"""
    Thank you for your message! 
    
    **Your request:** {prompt}
    
    🚧 **System Status:** The AI Executive Assistant is currently in setup mode.
    
    To enable full functionality:
    1. Implement agent logic in `app/agents/`
    2. Set up LangGraph workflows in `app/graph/`
    3. Configure tools in `app/tools/`
    4. Initialize RAG system in `app/rag/`
    
    Once these components are implemented, I'll be able to:
    - Process your requests intelligently
    - Access your emails and calendar
    - Perform research and provide insights
    - Remember context from our conversations
    
    For now, I'm here to confirm the system is working! 🎉
    """
    
    return response


def display_system_info():
    """Display system information"""
    if st.session_state.get('show_system_info', False):
        with st.expander("📊 System Information", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Environment")
                st.code(f"""
Python: {sys.version.split()[0]}
Ollama URL: {os.getenv('OLLAMA_BASE_URL')}
Model: {os.getenv('OLLAMA_MODEL')}
ChromaDB: {os.getenv('CHROMADB_PATH')}
                """)
            
            with col2:
                st.subheader("Project Structure")
                st.code("""
✓ app/graph/
✓ app/agents/
✓ app/tools/
✓ app/gmail/
✓ app/rag/
✓ app/memory/
✓ app/prompts/
✓ app/config/
✓ ui/
✓ tests/
                """)
        
        st.session_state.show_system_info = False


def main():
    """Main application entry point"""
    
    # Initialize session state
    initialize_session_state()
    
    # Display sidebar
    display_sidebar()
    
    # Display system info if requested
    display_system_info()
    
    # Display welcome message if no chat history
    if not st.session_state.messages:
        display_welcome_message()
    
    # Display chat interface
    display_chat_interface()
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: gray;'>"
        "AI Executive Assistant v1.0 | Built with LangGraph, LangChain & Streamlit"
        "</div>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()

# Made with Bob
