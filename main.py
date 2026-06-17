"""
AI Executive Assistant - Main Entry Point

This script initializes the AI Executive Assistant system, loads configuration,
and verifies all components are properly set up.
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv
from app.gmail import fetch_recent_emails, format_email_for_display

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log')
    ]
)

logger = logging.getLogger(__name__)


def load_environment():
    """Load environment variables from .env file"""
    env_path = Path('.env')
    if not env_path.exists():
        logger.error(".env file not found!")
        return False
    
    load_dotenv(env_path)
    logger.info("Environment variables loaded successfully")
    return True


def verify_ollama_connection():
    """Verify connection to Ollama server"""
    try:
        ollama_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
        ollama_model = os.getenv('OLLAMA_MODEL', 'llama3.2')
        
        logger.info(f"Ollama Configuration:")
        logger.info(f"  - Base URL: {ollama_url}")
        logger.info(f"  - Model: {ollama_model}")
        
        logger.info("Ollama configuration verified")
        return True
        
    except Exception as e:
        logger.error(f"Error verifying Ollama connection: {e}")
        return False


def verify_chromadb_setup():
    """Verify ChromaDB configuration"""
    try:
        chromadb_path = os.getenv('CHROMADB_PATH', './data/chromadb')
        collection_name = os.getenv('CHROMADB_COLLECTION_NAME', 'executive_assistant')
        
        logger.info(f"ChromaDB Configuration:")
        logger.info(f"  - Path: {chromadb_path}")
        logger.info(f"  - Collection: {collection_name}")
        
        Path(chromadb_path).mkdir(parents=True, exist_ok=True)
        logger.info("ChromaDB directory verified/created")
        return True
        
    except Exception as e:
        logger.error(f"Error verifying ChromaDB setup: {e}")
        return False


def verify_project_structure():
    """Verify all required directories exist"""
    required_dirs = [
        'app/graph',
        'app/agents',
        'app/tools',
        'app/gmail',
        'app/rag',
        'app/memory',
        'app/prompts',
        'app/config',
        'ui',
        'tests'
    ]
    
    logger.info("Verifying project structure...")
    all_exist = True
    
    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists():
            logger.info(f"  OK {dir_path}")
        else:
            logger.warning(f"  MISSING {dir_path}")
            all_exist = False
    
    return all_exist


def display_system_info():
    """Display system information and configuration"""
    logger.info("=" * 60)
    logger.info("AI EXECUTIVE ASSISTANT - SYSTEM INFORMATION")
    logger.info("=" * 60)
    
    logger.info(f"Python Version: {sys.version}")
    logger.info(f"Working Directory: {os.getcwd()}")
    logger.info(f"Log Level: {os.getenv('LOG_LEVEL', 'INFO')}")
    logger.info(f"Debug Mode: {os.getenv('DEBUG_MODE', 'False')}")
    
    logger.info("=" * 60)


def initialize_system():
    """Initialize the AI Executive Assistant system"""
    logger.info("Starting AI Executive Assistant initialization...")
    
    if not load_environment():
        logger.error("Failed to load environment variables")
        return False
    
    display_system_info()
    
    if not verify_project_structure():
        logger.warning("Some project directories are missing")
    
    if not verify_ollama_connection():
        logger.warning("Ollama connection verification failed")
    
    if not verify_chromadb_setup():
        logger.error("ChromaDB setup verification failed")
        return False
    
    return True


def fetch_and_display_emails():
    """Fetch and display recent emails from Gmail"""
    logger.info("=" * 60)
    logger.info("PHASE 1: BASIC EMAIL READER")
    logger.info("=" * 60)
    
    try:
        logger.info("Fetching recent emails from Gmail...")
        emails = fetch_recent_emails(max_results=5)
        
        if not emails:
            logger.warning("No emails found or unable to fetch emails.")
            logger.info("\nPlease ensure:")
            logger.info("  1. You have placed credentials.json in the project root")
            logger.info("  2. You have authorized the application")
            return False
        
        logger.info(f"\nSuccessfully fetched {len(emails)} emails!\n")
        
        # Display each email
        for i, email in enumerate(emails, 1):
            print(f"\n{'='*80}")
            print(f"EMAIL {i} of {len(emails)}")
            print(format_email_for_display(email))
        
        logger.info("=" * 60)
        logger.info("EMAIL FETCH COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)
        return True
        
    except FileNotFoundError as e:
        logger.error(f"\n{e}")
        return False
    except Exception as e:
        logger.error(f"Error fetching emails: {e}", exc_info=True)
        return False


def interactive_mode():
    """Run interactive chat mode with email agent"""
    from app.graph.email_workflow import run_email_conversation
    
    logger.info("=" * 60)
    logger.info("PHASE 2: INTERACTIVE EMAIL AGENT")
    logger.info("=" * 60)
    logger.info("")
    
    try:
        # Run the interactive conversation
        run_email_conversation()
        return True
    except Exception as e:
        logger.error(f"Error in interactive mode: {e}", exc_info=True)
        return False


def main():
    """Main entry point"""
    import sys
    
    try:
        if not initialize_system():
            logger.error("=" * 60)
            logger.error("SYSTEM INITIALIZATION FAILED")
            logger.error("=" * 60)
            return 1
        
        logger.info("=" * 60)
        logger.info("SYSTEM INITIALIZED SUCCESSFULLY")
        logger.info("=" * 60)
        logger.info("")
        
        # Check command line arguments
        if len(sys.argv) > 1:
            mode = sys.argv[1].lower()
            
            if mode == "phase1":
                # Phase 1: Basic email reader
                fetch_and_display_emails()
            elif mode == "phase2" or mode == "interactive":
                # Phase 2: Interactive agent mode
                interactive_mode()
            elif mode == "help":
                print("\nUsage: python main.py [mode]")
                print("\nModes:")
                print("  phase1       - Run Phase 1: Basic email reader (fetch and display)")
                print("  phase2       - Run Phase 2: Interactive email agent")
                print("  interactive  - Same as phase2")
                print("  help         - Show this help message")
                print("\nDefault (no mode): Run Phase 2 interactive mode")
            else:
                logger.warning(f"Unknown mode: {mode}")
                logger.info("Run 'python main.py help' for usage information")
        else:
            # Default: Run interactive mode (Phase 2)
            interactive_mode()
        
        logger.info("")
        logger.info("Next steps:")
        logger.info("  1. Ensure Ollama is running: ollama serve")
        logger.info("  2. Pull your preferred model: ollama pull llama3.2")
        logger.info("  3. Run the Streamlit UI: streamlit run app.py")
        logger.info("")
        return 0
            
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

# Made with Bob
