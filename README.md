# CLI Agent Graph Sandbox

A fun sandbox to setup and test LangGraph graphs. The sandbox integrates a graph discovery service to surface all registered graphs in the graph/ directory. The graph manager compiles discovered graphs and builds an in memory checkpointer for persisting conversations during runtime. A Textual UI allows for graph selection and multi-turn conversations via the graph with thread management. 

Tools can be added via the tools/ dir as well as via the mcp_config file. MCP Servers are setup during startup and are made available via the mcp_registry.
Langfuse is integrated as a callback for observability by the graph_manager. It is also integrated for prompt management, exiting graphs currently require a prompt key. 

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
- `TWILIO_ACCOUNT_SID` - Account SID
- `TWILIO_AUTH_TOKEN` - Auth Token
- `TWILIO_FROM_NUMBER` - Twilio Sender Number
- `TWILIO_TO_NUMBER` - Your number 

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
