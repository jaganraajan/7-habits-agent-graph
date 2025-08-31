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
- `GITHUB_TOKEN` – Your GitHub Personal Access Token for GitHub MCP integration

### 4. MCP Configuration

Copy the example mcp_config file and configure:

```bash
cp mcp_config.example.json mcp_config.json
```
The project includes two pre-configured MCP servers:

1. **Filesystem Server**: Pre-configured and auto-pulls its Docker image when needed. Provides 11 tools for file operations (read, write, edit, search, etc.) that agents can use through natural language.

2. **GitHub Server**: Pre-configured GitHub MCP server that provides 26 GitHub tools including:
   - Repository operations (list commits, pull requests, issues)
   - Code search across repositories  
   - File content retrieval
   - Issue and PR management
   - Repository creation and forking
   - And much more

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

### 6. Run the Demo
```bash
python main.py
```

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

## References

- [LangGraph](https://github.com/langchain-ai/langgraph)
- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)
- [LangFuse](https://github.com/langfuse/langfuse)
- [LangFuse Docs](https://langfuse.com/docs)
- [GitHub MCP Server](https://github.com/modelcontextprotocol/servers/tree/main/src/github)
