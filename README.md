## 7 Habits Agent Graphs

This repository contains agent graph implementations inspired by the "7 Habits" framework, using LangGraph and MCP tools. It provides both a CLI and a Flask web UI for experimenting with agentic workflows, vision board image generation, and GitHub/task management automation.

**Key Features:**
- Modular agent graph architecture (see `/graphs`)
- Modern Flask web UI with vision board and chat
- GitHub and Task management MCP server integration
- Langfuse observability and prompt management

**Two Interfaces Available:**
1. **Textual Terminal UI** - Interactive command-line interface with graph selection and multi-turn conversations
2. **Flask Web UI** - Modern web interface with vision board slideshow and AI chat features

This is a fun sandbox I customized to improve my skills in LangGraph. The sandbox integrates a graph discovery service to surface all registered graphs in the graph/ directory. The graph manager compiles discovered graphs and builds an in memory checkpointer for persisting conversations during runtime. 

Tools can be added via the tools/ dir as well as via the mcp_config file. MCP Servers are setup during startup and are made available via the mcp_registry.
Langfuse is integrated as a callback for observability by the graph_manager. It is also integrated for prompt management, existing graphs currently require a prompt key. 

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

**Azure OpenAI Configuration** (for vision board and chat):
- `AZURE_OPENAI_API_KEY` – Your Azure OpenAI API key
- `AZURE_OPENAI_ENDPOINT` – Your Azure OpenAI endpoint URL (e.g., https://your-resource.openai.azure.com/)
- `AZURE_OPENAI_DALLE_DEPLOYMENT` – Your DALL-E deployment name (defaults to "dall-e-3")
- `AZURE_OPENAI_DALLE_API_KEY` – Your Azure OpenAI DALL-E API key (if different from main API key)
- `AZURE_OPENAI_DALLE_ENDPOINT` – Your Azure OpenAI DALL-E endpoint URL

**Flask Web UI Configuration** (optional):
- `FLASK_SECRET_KEY` – Secret key for Flask sessions (defaults to development key)
- `FLASK_DEBUG=true` – Enable Flask debug mode for development
- `PORT=5000` – Port for the Flask web server
- `DATA_DIR=./data` – Directory for vision board images (defaults to ./data)

Optional (for enhanced capabilities):
- `PERPLEXITY_API_KEY` – Your Perplexity API key for web search capabilities via custom tool
- `LANGFUSE_PUBLIC_KEY` – Your LangFuse project's public API key
- `LANGFUSE_SECRET_KEY` – Your LangFuse project's secret API key  
- `LANGFUSE_HOST=http://localhost:3000` – LangFuse instance URL
```

### 4. MCP Configuration
Copy the example MCP config and configure:
```bash
cp mcp_config.example.json mcp_config.json
```

### 5. Run the Application

**Terminal UI:**
```bash
python main.py
```

**Flask Web UI:**
```bash
python web_app.py
```

Then open your browser to [http://localhost:5000](http://localhost:5000)

---

## Graphs Overview

This repository contains agent graph implementations inspired by the "7 Habits" framework. The `/graphs` directory includes a variety of graph modules, each representing a distinct workflow or habit-related process. The purpose of this section is to provide a clear overview of each graph's purpose and structure, complemented by illustrative diagrams.

### Graphs Directory Structure

- [`01-linear`](https://github.com/jaganraajan/7-habits-agent-graph/tree/main/graphs/01-linear):  
   A simple, linear workflow demonstrating sequential agent actions.  
   ```
   Step 1 → Step 2 → Step 3
   ```
   *Use case:* Demonstrates basic, stepwise automation.

- [`02-tooluse`](https://github.com/jaganraajan/7-habits-agent-graph/tree/main/graphs/02-tooluse):  
   Illustrates agent tool usage with branching logic.  
   ```
   Start
    │
    ├── Tool A
    │
    └── Tool B
   ```
   *Use case:* Showcases how agents can select and use different tools.

- [`06-github-info`](https://github.com/jaganraajan/7-habits-agent-graph/tree/main/graphs/06-github-info):  
   A graph focused on retrieving and summarizing GitHub information.  

   *Use case:* Automates gathering of repository/user data from GitHub.

### Configuration Notes

- **Without GITHUB_TOKEN**: Limited to public repository access
- **With GITHUB_TOKEN**: Full access to your repositories and enhanced API limits
- **Default Repository**: Commands default to `jaganraajan/7-habits-agent-graph` but can target any repository

## Using Vision Board Image Generation

The `07-vision-board` graph demonstrates Azure OpenAI DALL-E integration for creating inspiring vision board images.

### Azure OpenAI DALL-E Setup

1. **Create Azure OpenAI Resource:**
   - Go to Azure Portal and create an Azure OpenAI resource
   - Deploy a DALL-E model (dall-e-3 recommended)
   - Note your endpoint URL and API key

2. **Configure Environment Variables:**
   ```bash
   AZURE_OPENAI_API_KEY=your_azure_openai_api_key
   AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
   AZURE_OPENAI_DALLE_DEPLOYMENT=dall-e-3
   ```

### Getting Started with Vision Board

1. **Start the Application:**
   ```bash
   python main.py
   ```

2. **Select the right Graph:**
   - Choose `02-tooluse` from the workflow dropdown

3. **Try Sample Prompts:**
   - "Create a vision board showing career success with a corner office, certificates, and achievements"
   - "Generate an image representing health and fitness goals with running, healthy food, and strength"
   - "Design a vision for travel dreams with beautiful destinations, airplanes, and adventure scenes"
   - "Create a family and relationship vision with happy moments, love, and togetherness"

### Available Tools

- **`generate_vision_image`** - Direct tool for quick image generation

### Frontend Integration

The vision board agent returns structured data perfect for frontend integration:
- **Vision text**: The original prompt describing the vision
- **Local image path**: File path for displaying in web applications
- **Original URL**: Direct DALL-E URL (temporary)
- **Image metadata**: Size, timestamp, and other details

Images are saved in the `./data` directory by default and can be served by your frontend application.

## Using Task Management App MCP Integration

The Task Management app integration connects to an external MCP server to provide comprehensive task management capabilities. This demonstrates how to integrate with external HTTP-based MCP servers for extended functionality.

### MCP Server Configuration

The task management app requires an external MCP server. The server configuration is already included in `mcp_config.json`:

```json
{
  "mcpServers": {
    "task": {
      "transport": "sse",
      "url": "http://localhost:3000/mcp"
    }
  }
}
```

### Prerequisites

1. **External Task management MCP Server**: You need to have a compatible MCP server running at `http://<external-server-link>/mcp` that provides the following tools:
   - `add_task` - Add new Task items
   - `list_tasks` - List all Task items  
   - `complete_task` - Mark Tasks as completed
   - `delete_task` - Delete Task items

2. **Environment Setup**: Ensure your Azure OpenAI credentials are configured in `.env` for the chat functionality.

### Configuration Notes

- **MCP Server Connection**: Requires external MCP server running on Azure container apps for example
- **Transport Protocol**: Uses Server-Sent Events (SSE) for communication
- **Error Handling**: If the MCP server is unavailable, the graph will gracefully handle errors
- **Natural Language**: The AI agent interprets natural language requests and maps them to appropriate Task operations

## References

- [LangGraph](https://github.com/langchain-ai/langgraph)
- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)
- [LangFuse](https://github.com/langfuse/langfuse)
- [LangFuse Docs](https://langfuse.com/docs)
- [GitHub MCP Server](https://github.com/modelcontextprotocol/servers/tree/main/src/github)
