# Agent Platform - Python + LangChain + LangGraph

A production-ready AI agent platform for building B2C products with minimal human intervention.

## Tech Stack
- **Python 3.11+** - Core language
- **FastAPI** - High-performance async API
- **LangChain** - LLM orchestration
- **LangGraph** - Stateful agent workflows
- **Anthropic Claude** - Primary LLM
- **PostgreSQL** - Data persistence
- **Redis** - Caching and queues

## Project Structure
```
agent-platform-python/
├── app/
│   ├── core/           # Core platform components
│   ├── agents/         # Agent implementations
│   ├── tools/          # LangChain tools
│   ├── graphs/         # LangGraph workflows
│   └── api/            # FastAPI routes
├── tests/
└── main.py
```

## Quick Start
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Add your API keys

# Run development server
uvicorn main:app --reload --port 8000
```

## API Endpoints
- `POST /api/chat` - Process user message
- `GET /api/health` - Health check
- `GET /api/session/{session_id}` - Get session history