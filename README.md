# Workshop on LangGraph & LangFuse

In this workshop, we'll be looking at a simple LangGraph & Langfuse integration example. We'll touch on basic agents, patterns and observability.

## Quick Start

### 1. Install Dependencies
```bash
uv sync
```

### 2. Activate Virtual Environment
```bash
source .venv/bin/activate
```

### 3. Environment Setup
Copy the example environment file and configure:

```bash
cp env.example .env
```

Required variables in `.env`:
- `OPENAI_API_KEY` – Your OpenAI API key
- `MCP_WORKING_DIR=./data` – Directory for MCP filesystem server (defaults to project root)

Optional (for enhanced capabilities):
- `PERPLEXITY_API_KEY` – Your Perplexity API key for web search capabilities via custom tool
- `LANGFUSE_PUBLIC_KEY` – Your LangFuse project's public API key
- `LANGFUSE_SECRET_KEY` – Your LangFuse project's secret API key  
- `LANGFUSE_HOST=http://localhost:3000` – LangFuse instance URL

### 4. MCP Configuration

Copy the example mcp_config file and configure:

```bash
cp mcp_config.example.json mcp_config.json
```
The project includes:

1. **Filesystem Server**: Pre-configured and auto-pulls its Docker image when needed. Provides 11 tools for file operations (read, write, edit, search, etc.) that agents can use through natural language.

### 5. LangFuse Setup (Optional)
For observability and tracing:

```bash
git clone git@github.com:langfuse/langfuse.git
cd langfuse
docker-compose up
```

Connect to [http://localhost:3000](http://localhost:3000) and create a project for API keys.

### 6. Run the Demo
```bash
python main.py
```

## References

- [LangGraph](https://github.com/langchain-ai/langgraph)
- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)
- [LangFuse](https://github.com/langfuse/langfuse)
- [LangFuse Docs](https://langfuse.com/docs)