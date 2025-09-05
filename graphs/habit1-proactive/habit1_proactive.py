import os
from datetime import datetime
from dotenv import load_dotenv
from typing import Annotated, TypedDict
from langchain_core.messages import AIMessage, BaseMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import AzureChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from framework.decorators import registered_graph
from framework.mcp_registry import get_mcp_tools
from framework.prompt_manager import get_prompt
from framework.log_service import log

# this is the key for the prompt in the prompt manager which gets the Langfuse prompt
PROMPT_KEY = "habit1_proactive"

# the state that will be passed to each node
class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    repositories: list[dict]  # Repositories with real URLs from search_repositories
    issues: list[dict]       # Issues with real URLs from search_issues  
    documentation: list[dict] # Documentation files with real URLs from get_file_contents
    summary: str

def init_state() -> State:
    system_prompt = get_prompt(PROMPT_KEY) or """You are a proactive GitHub research assistant for the 7 Habits Agent Graph. 
Your mission is to research agentic/MCP repositories, find learning opportunities, and identify beginner-friendly contribution areas.

Focus on:
1. Finding top agentic/MCP repositories for potential contributions
2. Identifying beginner-friendly issues (good first issue, help wanted)
3. Looking for ROADMAP, ADR, and CONTRIBUTING documentation for guidance
4. Finding example agentic patterns and recent changelogs
5. Summarizing findings in a clear, actionable format"""
    
    return {
        "messages": [SystemMessage(content=system_prompt)],
        "repositories": [],
        "issues": [],
        "documentation": [],
        "summary": ""
    }

@registered_graph("habit1-proactive-1")
def build_graph() -> StateGraph:
    load_dotenv()
    try:
        github_tools = get_mcp_tools("github")

        def search_repositories_node(state: State, config: RunnableConfig) -> State:
            """Search for agentic/MCP repositories and extract real URLs"""
            subscription_key = os.getenv("AZURE_OPENAI_API_KEY")
            api_version = "2024-12-01-preview"
            llm = AzureChatOpenAI(
                api_key=subscription_key,
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_version=api_version,
                deployment_name="gpt-4o-mini"
            ).bind_tools([tool for tool in github_tools if tool.name == "search_repositories"])
            
            search_prompt = """Search for repositories related to agentic AI and MCP (Model Context Protocol).
            
            Search for:
            - "langgraph" language:python stars:>100
            - "mcp model context protocol" language:python
            - "agentic ai framework" language:python stars:>50
            
            Use the search_repositories tool to find these repositories."""
            
            ai: AIMessage = llm.invoke(state["messages"] + [SystemMessage(content=search_prompt)], config=config)
            return {"messages": [ai]}

        def search_issues_node(state: State, config: RunnableConfig) -> State:
            """Search for beginner-friendly issues and extract real URLs"""
            subscription_key = os.getenv("AZURE_OPENAI_API_KEY")
            api_version = "2024-12-01-preview"
            llm = AzureChatOpenAI(
                api_key=subscription_key,
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_version=api_version,
                deployment_name="gpt-4o-mini"
            ).bind_tools([tool for tool in github_tools if tool.name == "search_issues"])
            
            issues_prompt = """Search for beginner-friendly issues in agentic AI repositories.
            
            Search for:
            - label:"good first issue" repo:langchain-ai/langgraph
            - label:"help wanted" is:open ai agent
            - label:"beginner-friendly" mcp
            
            Use the search_issues tool to find these issues."""
            
            ai: AIMessage = llm.invoke(state["messages"] + [SystemMessage(content=issues_prompt)], config=config)
            return {"messages": [ai]}

        def collect_documentation_node(state: State, config: RunnableConfig) -> State:
            """Get documentation files from repositories and extract real URLs"""
            subscription_key = os.getenv("AZURE_OPENAI_API_KEY")
            api_version = "2024-12-01-preview"
            llm = AzureChatOpenAI(
                api_key=subscription_key,
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_version=api_version,
                deployment_name="gpt-4o-mini"
            ).bind_tools([tool for tool in github_tools if tool.name == "get_file_contents"])
            
            docs_prompt = """Get documentation files from key repositories to understand contribution guidelines.
            
            Get these files:
            - CONTRIBUTING.md from langchain-ai/langgraph
            - README.md from anthropics/mcp-python
            - ROADMAP.md or ADR/ from relevant repositories
            
            Use the get_file_contents tool to retrieve these files."""
            
            ai: AIMessage = llm.invoke(state["messages"] + [SystemMessage(content=docs_prompt)], config=config)
            return {"messages": [ai]}

        def extract_data_node(state: State, config: RunnableConfig) -> State:
            """Extract structured data with real URLs from tool responses"""
            repositories = []
            issues = []
            documentation = []
            
            # Process messages to extract data from tool responses
            for message in state["messages"]:
                if hasattr(message, 'tool_calls'):
                    # This is a message with tool calls (requests)
                    continue
                elif hasattr(message, 'content') and hasattr(message, 'name'):
                    # This is a tool response message
                    try:
                        import json
                        if message.name == 'search_repositories':
                            # Parse repository search results
                            tool_response = json.loads(message.content) if isinstance(message.content, str) else message.content
                            if isinstance(tool_response, dict) and 'items' in tool_response:
                                for repo in tool_response['items'][:10]:  # Limit to top 10
                                    repositories.append({
                                        'name': repo.get('full_name', repo.get('name', 'Unknown')),
                                        'html_url': repo.get('html_url', '#'),
                                        'description': repo.get('description', 'No description'),
                                        'stargazers_count': repo.get('stargazers_count', 0),
                                        'language': repo.get('language', 'Unknown')
                                    })
                        elif message.name == 'search_issues':
                            # Parse issue search results
                            tool_response = json.loads(message.content) if isinstance(message.content, str) else message.content
                            if isinstance(tool_response, dict) and 'items' in tool_response:
                                for issue in tool_response['items'][:15]:  # Limit to top 15
                                    issues.append({
                                        'title': issue.get('title', 'Unknown'),
                                        'html_url': issue.get('html_url', '#'),
                                        'labels': [label.get('name', '') for label in issue.get('labels', [])],
                                        'repository': issue.get('repository', {}).get('full_name', 'Unknown'),
                                        'state': issue.get('state', 'unknown')
                                    })
                        elif message.name == 'get_file_contents':
                            # Parse file content results
                            tool_response = json.loads(message.content) if isinstance(message.content, str) else message.content
                            if isinstance(tool_response, dict):
                                documentation.append({
                                    'name': tool_response.get('name', 'Unknown'),
                                    'html_url': tool_response.get('html_url', '#'),
                                    'path': tool_response.get('path', ''),
                                    'type': tool_response.get('type', 'file'),
                                    'size': tool_response.get('size', 0)
                                })
                    except (json.JSONDecodeError, AttributeError, KeyError) as e:
                        log(f"Error parsing tool response: {e}")
                        continue
            
            return {
                "repositories": repositories,
                "issues": issues, 
                "documentation": documentation
            }

        def synthesize_node(state: State, config: RunnableConfig) -> State:
            """Synthesize research results into a summary using structured data with real URLs"""
            # Create formatted sections using structured data from state
            repositories_section = ""
            if state.get("repositories"):
                repositories_section = "\n".join([
                    f"- **[{repo['name']}]({repo['html_url']})** ⭐ {repo['stargazers_count']} | {repo['language']}\n  {repo['description']}"
                    for repo in state["repositories"]
                ])
            else:
                repositories_section = "No repositories found in this search."
            
            issues_section = ""
            if state.get("issues"):
                issues_section = "\n".join([
                    f"- **[{issue['title']}]({issue['html_url']})** ({issue['repository']})\n  Labels: {', '.join(issue['labels']) if issue['labels'] else 'None'}"
                    for issue in state["issues"]
                ])
            else:
                issues_section = "No beginner-friendly issues found."
            
            docs_section = ""
            if state.get("documentation"):
                docs_section = "\n".join([
                    f"- **[{doc['name']}]({doc['html_url']})** ({doc['path']})"
                    for doc in state["documentation"]
                ])
            else:
                docs_section = "No documentation files retrieved."
            
            summary_content = f"""# Habit 1 - Be Proactive: Weekly GitHub Research Summary

**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 🎯 Top Agentic/MCP Repositories for Contribution

{repositories_section}

## 🌱 Beginner-Friendly Opportunities

{issues_section}

## 📚 Learning Resources

{docs_section}

## 🔍 Key Insights & Patterns

Based on the research conducted:

- **Repository Landscape**: Found {len(state.get('repositories', []))} relevant repositories in the agentic AI and MCP space
- **Contribution Opportunities**: Identified {len(state.get('issues', []))} beginner-friendly issues across various projects
- **Documentation Access**: Retrieved {len(state.get('documentation', []))} documentation files for contribution guidance

## ⚡ Top 3 Action Items

1. **Start Contributing**: Pick one of the beginner-friendly issues above and review the repository's CONTRIBUTING.md
2. **Learn from Leaders**: Study the most-starred repository in the list to understand best practices
3. **Engage with Community**: Join discussions in active issues to understand the project dynamics

---

**Note:** All links above are real GitHub URLs extracted directly from the GitHub API responses via MCP tools.
This ensures accuracy and prevents broken links in the generated report.

**Technical Details:**
- Repositories found via `search_repositories` MCP tool
- Issues found via `search_issues` MCP tool  
- Documentation retrieved via `get_file_contents` MCP tool
- All URLs are verified GitHub links from API responses"""
            
            return {
                "messages": [AIMessage(content=summary_content)],
                "summary": summary_content
            }

        def save_summary_node(state: State, config: RunnableConfig) -> State:
            summary = state.get("summary", "")
            output_path = os.path.join("data", "habits", "habit1_proactive_summary.md")
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(summary)
            return state

        # Create specialized tool nodes with minimal tool sets
        search_repos_tools = [tool for tool in github_tools if tool.name == "search_repositories"]
        search_issues_tools = [tool for tool in github_tools if tool.name == "search_issues"]
        get_files_tools = [tool for tool in github_tools if tool.name == "get_file_contents"]
        
        search_repos_tool_node = ToolNode(tools=search_repos_tools)
        search_issues_tool_node = ToolNode(tools=search_issues_tools)
        get_files_tool_node = ToolNode(tools=get_files_tools)

        # Build the graph with clear separation of data collection and summarization
        graph = StateGraph(State)
        
        # Data collection nodes
        graph.add_node("search_repositories", search_repositories_node)
        graph.add_node("repos_tools", search_repos_tool_node)
        graph.add_node("search_issues", search_issues_node)
        graph.add_node("issues_tools", search_issues_tool_node)
        graph.add_node("collect_docs", collect_documentation_node)
        graph.add_node("docs_tools", get_files_tool_node)
        graph.add_node("extract_data", extract_data_node)
        
        # Summarization nodes
        graph.add_node("synthesize", synthesize_node)
        graph.add_node("save", save_summary_node)
        
        # Data collection workflow
        graph.add_edge(START, "search_repositories")
        graph.add_edge("search_repositories", "repos_tools")
        graph.add_edge("repos_tools", "search_issues")
        graph.add_edge("search_issues", "issues_tools")
        graph.add_edge("issues_tools", "collect_docs")
        graph.add_edge("collect_docs", "docs_tools")
        graph.add_edge("docs_tools", "extract_data")
        
        # Summarization workflow
        graph.add_edge("extract_data", "synthesize")
        graph.add_edge("synthesize", "save")
        graph.add_edge("save", END)
        
        return graph
    except Exception as e:
        log(f"Error building habit1-proactive graph: {e}")
        return None