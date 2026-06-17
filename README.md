# AI Executive Assistant

An intelligent AI-powered executive assistant built with LangGraph, LangChain, and Streamlit. This system helps manage emails, tasks, and provides intelligent assistance through a conversational interface.

## Features

- 🤖 **Multi-Agent Architecture**: Built with LangGraph for sophisticated agent orchestration
- 📧 **Gmail Integration**: Automated email management and responses
- 💬 **Conversational Interface**: Streamlit-based web UI for natural interactions
- 🧠 **RAG System**: Retrieval-Augmented Generation using ChromaDB for context-aware responses
- 🔄 **Memory Management**: Persistent conversation history and context
- 🎯 **Task Management**: Intelligent task tracking and prioritization
- 🔍 **Research Capabilities**: Web search and information gathering

## Architecture

```
AI_Executive_Assistant/
├── app/
│   ├── graph/          # LangGraph workflow definitions
│   ├── agents/         # Agent implementations
│   ├── tools/          # Tool functions for agents
│   ├── gmail/          # Gmail API integration
│   ├── rag/            # RAG system components
│   ├── memory/         # Memory and state management
│   ├── prompts/        # System and agent prompts
│   └── config/         # Configuration files
├── ui/                 # Streamlit UI components
├── tests/              # Unit and integration tests
├── main.py             # Backend initialization
├── app.py              # Streamlit web interface
├── .env                # Environment variables
└── requirements.txt    # Python dependencies
```

## Prerequisites

- Python 3.11.9
- Ollama (for local LLM inference)
- Google API credentials (for Gmail integration)

## Installation

1. **Clone the repository** (if applicable):

   ```bash
   cd C:\Users\AshishManjhi\Documents\Projects\LLM-Projects\AI_Executive_Assistant
   ```

2. **Create and activate virtual environment**:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   - Copy `.env` and update with your credentials
   - Set up Ollama base URL and model
   - Add Google API credentials for Gmail integration

5. **Install and run Ollama**:
   ```bash
   # Download from https://ollama.ai
   ollama pull llama3.2  # or your preferred model
   ollama serve
   ```

## Usage

### Running the Backend

Initialize the system and verify configuration:

```bash
python main.py
```

### Running the Streamlit UI

Launch the web interface:

```bash
streamlit run app.py
```

The application will be available at `http://localhost:8501`

## Configuration

### Environment Variables

Edit `.env` file to configure:

- **Ollama Settings**: Base URL and model selection
- **Google API**: Client ID, secret, and redirect URI
- **ChromaDB**: Database path and collection name
- **Application**: Log level and debug mode
- **Streamlit**: Server port and address

### Gmail API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Gmail API
4. Create OAuth 2.0 credentials
5. Download credentials and update `.env`

## Development

### Project Structure

- **app/graph/**: Define LangGraph workflows and state machines
- **app/agents/**: Implement specialized agents (email, task, research)
- **app/tools/**: Create tool functions that agents can use
- **app/rag/**: Set up RAG system with ChromaDB
- **app/memory/**: Implement conversation and context memory
- **ui/**: Build Streamlit UI components

### Adding New Agents

1. Create agent file in `app/agents/`
2. Define agent logic and prompts
3. Register agent in LangGraph workflow
4. Add corresponding tools if needed

### Testing

Run tests with pytest:

```bash
pytest tests/
```

## Technology Stack

- **LangGraph**: Agent orchestration and workflow management
- **LangChain**: LLM framework and abstractions
- **Ollama**: Local LLM inference
- **ChromaDB**: Vector database for RAG
- **Streamlit**: Web UI framework
- **Python 3.11.9**: Core programming language

## Roadmap

- [ ] Calendar integration
- [ ] Advanced task management
- [ ] Multi-language support
- [ ] Voice interface
- [ ] Mobile app
- [ ] Advanced analytics dashboard

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues, questions, or contributions, please open an issue on the repository.

## Acknowledgments

- LangChain team for the excellent framework
- Ollama for local LLM capabilities
- Streamlit for the intuitive UI framework
