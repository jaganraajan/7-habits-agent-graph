# CLI Agent Graph Sandbox

A fun sandbox to setup and test LangGraph graphs. The sandbox integrates a graph discovery service to surface all registered graphs in the graph/ directory. The graph manager compiles discovered graphs and builds an in memory checkpointer for persisting conversations during runtime. 

**Two Interfaces Available:**
1. **Textual Terminal UI** - Interactive command-line interface with graph selection and multi-turn conversations
2. **Flask Web UI** - Modern web interface with vision board slideshow and AI chat features

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
cp env.example .env
```

Required variables in `.env`:
- `OPENAI_API_KEY` – Your OpenAI API key
- `MCP_WORKING_DIR=./data` – Directory for MCP filesystem server (defaults to project root)

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
- `TWILIO_ACCOUNT_SID` - Account SID
- `TWILIO_AUTH_TOKEN` - Auth Token
- `TWILIO_FROM_NUMBER` - Twilio Sender Number
- `TWILIO_TO_NUMBER` - Your number 
- `GITHUB_TOKEN` – Your GitHub Personal Access Token for GitHub MCP integration

### 4. MCP Configuration

Copy the example mcp_config file and configure:

```bash
cp mcp_config.example.json mcp_config.json
```
The project includes four pre-configured MCP servers:

1. **Filesystem Server**: Pre-configured and auto-pulls its Docker image when needed. Provides 11 tools for file operations (read, write, edit, search, etc.) that agents can use through natural language.

2. **GitHub Server**: Pre-configured GitHub MCP server that provides 26 GitHub tools including:
   - Repository operations (list commits, pull requests, issues)
   - Code search across repositories  
   - File content retrieval
   - Issue and PR management
   - Repository creation and forking
   - And much more

3. **Vision Server**: Local Python MCP server that provides vision board image generation using Azure OpenAI DALL-E:
   - `vision/add_with_image` - Generate vision board images from text descriptions
   - Supports multiple image sizes (1024x1024, 1792x1024, 1024x1792)
   - Saves images locally for frontend integration
   - Returns both vision text and image URLs

4. **TODO Server**: External HTTP MCP server for task management:
   - `add_todo_prompt` - Add new TODO items
   - `list_todos_prompt` - List all TODO items
   - `complete_todo_prompt` - Mark TODOs as completed
   - `delete_todo_prompt` - Delete TODO items
   - Connects to `http://localhost:3000/mcp` via SSE transport

#### GitHub MCP Setup

To enable GitHub integration:

1. Get a GitHub Personal Access Token:
   - Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
   - Click "Generate new token (classic)"
   - Select scopes based on your needs (repo access, user info, etc.)
   - Copy the generated token

2. Add your token to `.env`:
   ```bash
   GITHUB_TOKEN=your_github_token_here
   ```

The GitHub MCP server will automatically connect when you start the application.

### 5. LangFuse Setup (Optional)
For observability and tracing:

```bash
git clone git@github.com:langfuse/langfuse.git
cd langfuse
docker-compose up
```

Connect to [http://localhost:3000](http://localhost:3000) and create a project for API keys.

### 6. Run the Application

#### Option 1: Terminal UI (Original Interface)
```bash
python main.py
```

#### Option 2: Flask Web UI (New Web Interface)
```bash
python web_app.py
```

Then open your browser to [http://localhost:5000](http://localhost:5000)

## Flask Web UI Features

![Flask Web UI Screenshot](https://github.com/user-attachments/assets/9b2e369e-5008-4a01-a597-7bbd1c25fae9)

The Flask web application provides a modern web interface with two main features:

### 1. Vision Board Images Slideshow
- **Automatic Display**: Shows all images from the `data/` directory as an interactive slideshow
- **Navigation Controls**: Previous/Next buttons, image counter, and auto-play functionality
- **Real-time Updates**: Automatically refreshes to show newly generated images
- **Image Metadata**: Displays filename and creation timestamp for each image
- **Responsive Design**: Works on desktop and mobile devices

**Slideshow Controls:**
- ← → **Navigation buttons**: Move between images manually
- **Auto button**: Enable/disable automatic slideshow (3-second intervals)
- **Refresh button**: Manually check for new images
- **Image counter**: Shows current position (e.g., "2 / 3")

### 2. AI Chat Interface
- **Real-time Chat**: Interact with the 02-tooluse agent graph through a web interface
- **Vision Board Integration**: When you ask to create images, they automatically appear in the slideshow
- **Session Management**: Maintains conversation context within each chat session
- **New Chat**: Start fresh conversations anytime
- **Error Handling**: Graceful handling of configuration issues with helpful error messages

**Chat Features:**
- Message history for each session
- Timestamps for all messages
- Loading indicators during AI processing
- Automatic detection of image generation requests
- Integration with existing LangGraph framework

### Key Integration Points

**New Image Priority**: When the AI generates a new vision board image (via prompts like "create a vision board image" or "add image"), the newly created image automatically appears first in the slideshow, making it immediately visible.

**Reuses Existing Infrastructure**: The Flask app integrates with:
- Existing `framework/graph_manager.py` for chat processing
- Existing `tools/generate_vision_image.py` for image generation
- Existing MCP registry and configuration system
- Same environment variables and Azure OpenAI setup

### Usage Examples

1. **Generate Vision Board Images**:
   - Type: "Create a vision board image of career success"
   - The AI will generate an image and save it to the data/ folder
   - The new image appears first in the slideshow automatically

2. **Browse Existing Images**:
   - Use navigation controls to browse through existing vision board images
   - Enable auto-play to cycle through images automatically

3. **Ask Questions**:
   - Type any question to interact with the AI assistant
   - The same 02-tooluse agent graph powers both terminal and web interfaces

## Using GitHub MCP Integration

The `06-github-info` graph demonstrates GitHub MCP integration, providing natural language access to GitHub operations.

### Available GitHub Operations

The GitHub MCP server provides 26 tools for comprehensive GitHub interaction:

**Repository Information:**
- `list_commits` - Get recent commits from a repository
- `list_pull_requests` - List and filter repository pull requests  
- `list_issues` - List issues with filtering options
- `get_file_contents` - Get contents of files or directories

**Search Operations:**
- `search_repositories` - Search for GitHub repositories
- `search_code` - Search for code across GitHub repositories
- `search_issues` - Search for issues and pull requests
- `search_users` - Search for GitHub users

**Repository Management:**
- `create_repository` - Create new repositories
- `fork_repository` - Fork repositories to your account
- `create_branch` - Create new branches

**Issue & PR Management:**
- `create_issue` - Create new issues
- `update_issue` - Update existing issues
- `add_issue_comment` - Add comments to issues
- `create_pull_request` - Create new pull requests
- `merge_pull_request` - Merge pull requests
- `create_pull_request_review` - Review pull requests

**File Operations:**
- `create_or_update_file` - Create or update individual files
- `push_files` - Push multiple files in a single commit

### Sample Queries

Try these natural language queries with the `06-github-info` graph:

#### Repository Information
```
"Show me the recent commits and pull requests for this repository"
"List the latest 5 commits in jaganraajan/7-habits-agent-graph"
"What are the open pull requests for this repo?"
```

#### Search Operations  
```
"Search for Python repositories related to LangGraph"
"Find issues about MCP integration in langchain repositories"
"Search for code that uses 'StateGraph' in this repository"
```

#### Repository Analysis
```
"Get the README file from the main branch"
"Show me all Python files in the graphs directory"
"List all open issues labeled as 'bug'"
```

#### Development Workflow
```
"Create a new issue titled 'Add documentation for feature X'"
"Fork the repository langchain-ai/langgraph"
"Create a new branch called 'feature/new-integration'"
```

### Getting Started with GitHub Integration

1. **Start the Application:**
   ```bash
   python main.py
   ```

2. **Select the GitHub Info Graph:**
   - Choose `06-github-info` from the workflow dropdown

3. **Try Sample Queries:**
   - Start with: "Show me recent commits and pull requests for this repository"
   - Explore: "Search for repositories with topic 'agent-graph'"
   - Experiment: "List issues in this repository"

4. **Natural Language Interface:**
   - The AI agent can understand complex GitHub queries
   - It will automatically choose the appropriate GitHub tools
   - Results are formatted in a readable way

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

2. **Select the Vision Board Graph:**
   - Choose `07-vision-board` from the workflow dropdown

3. **Try Sample Prompts:**
   - "Create a vision board showing career success with a corner office, certificates, and achievements"
   - "Generate an image representing health and fitness goals with running, healthy food, and strength"
   - "Design a vision for travel dreams with beautiful destinations, airplanes, and adventure scenes"
   - "Create a family and relationship vision with happy moments, love, and togetherness"

### Available Tools

- **`generate_vision_image`** - Direct tool for quick image generation
- **`vision/add_with_image`** - MCP tool for vision board entries with metadata

### Frontend Integration

The vision board agent returns structured data perfect for frontend integration:
- **Vision text**: The original prompt describing the vision
- **Local image path**: File path for displaying in web applications
- **Original URL**: Direct DALL-E URL (temporary)
- **Image metadata**: Size, timestamp, and other details

Images are saved in the `./data` directory by default and can be served by your frontend application.

## Using TODO App MCP Integration

The TODO app integration connects to an external MCP server to provide comprehensive task management capabilities. This demonstrates how to integrate with external HTTP-based MCP servers for extended functionality.

### MCP Server Configuration

The TODO app requires an external MCP server running at `http://localhost:3000/mcp`. The server configuration is already included in `mcp_config.json`:

```json
{
  "mcpServers": {
    "todo": {
      "transport": "sse",
      "url": "http://localhost:3000/mcp"
    }
  }
}
```

### Prerequisites

1. **External TODO MCP Server**: You need to have a compatible MCP server running at `http://localhost:3000/mcp` that provides the following tools:
   - `add_todo_prompt` - Add new TODO items
   - `list_todos_prompt` - List all TODO items  
   - `complete_todo_prompt` - Mark TODOs as completed
   - `delete_todo_prompt` - Delete TODO items

2. **Environment Setup**: Ensure your Azure OpenAI credentials are configured in `.env` for the chat functionality.

### Getting Started with TODO App

1. **Start your TODO MCP Server:**
   ```bash
   # Start your external MCP server on port 3000
   # This should expose an MCP endpoint at http://localhost:3000/mcp
   ```

2. **Start the Application:**
   ```bash
   python main.py
   ```

3. **Select the TODO App Graph:**
   - Choose `08-todo-app` from the workflow dropdown

4. **Try Sample Queries:**
   - Start with: "Show me all my TODO items"
   - Add items: "Add a new TODO: Buy groceries"
   - Complete tasks: "Mark TODO item 1 as completed"
   - Delete items: "Delete TODO item 2"

### Available TODO Operations

The TODO app provides four main operations through natural language:

**Task Management:**
- `add_todo_prompt` - Add a new TODO item by providing a title
- `list_todos_prompt` - Retrieve all TODO items
- `complete_todo_prompt` - Mark a TODO item as completed by ID
- `delete_todo_prompt` - Delete a TODO item by ID

### Sample Queries

Try these natural language queries with the `08-todo-app` graph:

#### Adding TODOs
```
"Add a new TODO: Buy groceries"
"Create a task: Call dentist for appointment"
"Add to my list: Review quarterly report"
```

#### Viewing TODOs
```
"Show me all my TODO items"
"List all my tasks"
"What do I need to do?"
```

#### Completing TODOs
```
"Mark TODO item 1 as completed"
"Complete task number 3"
"Mark the grocery shopping as done"
```

#### Deleting TODOs
```
"Delete TODO item 2"
"Remove task number 5"
"Delete the completed grocery task"
```

### Exported Prompts

The TODO app exports the following prompt definitions (available in `prompts.py`):

```python
prompts = [
    {
        "id": "add_todo_prompt",
        "label": "Add TODO",
        "description": "Provide a title for the new TODO item.",
        "inputExample": {"title": "Buy groceries"}
    },
    {
        "id": "list_todos_prompt",
        "label": "List TODOs", 
        "description": "Retrieve the list of all TODO items.",
        "inputExample": {}
    },
    {
        "id": "complete_todo_prompt",
        "label": "Complete TODO",
        "description": "Mark a TODO item as completed by providing its ID.",
        "inputExample": {"id": 1}
    },
    {
        "id": "delete_todo_prompt",
        "label": "Delete TODO",
        "description": "Delete a TODO item by providing its ID.", 
        "inputExample": {"id": 1}
    }
]
```

### Configuration Notes

- **MCP Server Connection**: Requires external MCP server running on localhost:3000
- **Transport Protocol**: Uses Server-Sent Events (SSE) for communication
- **Error Handling**: If the MCP server is unavailable, the graph will gracefully handle errors
- **Natural Language**: The AI agent interprets natural language requests and maps them to appropriate TODO operations

## References

- [LangGraph](https://github.com/langchain-ai/langgraph)
- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)
- [LangFuse](https://github.com/langfuse/langfuse)
- [LangFuse Docs](https://langfuse.com/docs)
- [GitHub MCP Server](https://github.com/modelcontextprotocol/servers/tree/main/src/github)
