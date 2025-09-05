import os
import json
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
from framework.github_utils import (
    extract_github_links_from_messages,
    format_github_links_for_markdown,
    extract_actionable_items_from_tool_response
)

# this is the key for the prompt in the prompt manager which gets the Langfuse prompt
PROMPT_KEY = "habit6_synergize"

# the state that will be passed to each node
class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    github_links: list[str]
    integration_examples: list[dict]
    summary: str

def init_state() -> State:
    system_prompt = get_prompt(PROMPT_KEY) or """You are a GitHub research assistant focused on synergistic integration patterns and multi-tool collaboration in software development.

Your mission is to find excellent examples of repositories and projects that effectively combine multiple tools, technologies, and approaches to create value greater than the sum of parts.

Focus areas:
1. Multi-tool integration patterns (CI/CD, monitoring, testing, etc.)
2. Cross-functional collaboration examples
3. Repositories that combine different technologies synergistically
4. Workflow integrations that create multiplicative value
5. Examples of teams working across tool boundaries effectively

Look for patterns where projects:
- Integrate multiple development tools seamlessly
- Combine different programming languages or frameworks effectively
- Create workflows that amplify team productivity
- Show evidence of cross-functional collaboration
- Demonstrate tool chains that work better together than separately"""
    
    return {
        "messages": [SystemMessage(content=system_prompt)],
        "github_links": [],
        "integration_examples": [],
        "summary": ""
    }

@registered_graph("habit6-synergize")
def build_graph() -> StateGraph:
    load_dotenv()
    try:
        github_tools = get_mcp_tools("github")

        def data_collection_node(state: State, config: RunnableConfig) -> State:
            """Collect data focused on synergistic integration patterns"""
            subscription_key = os.getenv("AZURE_OPENAI_API_KEY")
            api_version = "2024-12-01-preview"
            llm = AzureChatOpenAI(
                api_key=subscription_key,
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_version=api_version,
                deployment_name="gpt-4o-mini"
            ).bind_tools(github_tools)
            
            research_prompt = """
Search for repositories that demonstrate excellent multi-tool integration and synergistic collaboration patterns.

SEARCH TARGETS:
1. Look for repositories with complex CI/CD workflows (.github/workflows/)
2. Search for projects that integrate multiple programming languages
3. Find repositories with comprehensive tool integration (monitoring, testing, deployment)
4. Look for examples of successful microservices architectures
5. Search for projects with extensive automation and tool coordination

Use these specific search queries:
- search_repositories: query="microservices OR multi-tool OR workflow integration"
- search_code: query=".github/workflows complex OR multi-language project"
- search_repositories: query="topic:devops OR topic:integration OR topic:automation"
- get_file_contents: Look for docker-compose.yml, .github/workflows/, Makefile, package.json with scripts
- search_repositories: query="polyglot OR multiple languages OR tool integration"

Focus on finding examples where multiple tools work together to create greater value.
"""
            
            research_message = SystemMessage(content=research_prompt)
            ai: AIMessage = llm.invoke(state["messages"] + [research_message], config=config)
            return {"messages": [ai]}

        def link_extraction_node(state: State, config: RunnableConfig) -> State:
            """Extract GitHub links and integration examples from tool responses"""
            github_links = extract_github_links_from_messages(state["messages"])
            
            # Extract integration examples
            integration_examples = []
            if state["messages"]:
                last_message = state["messages"][-1]
                if isinstance(last_message, AIMessage) and hasattr(last_message, 'tool_calls'):
                    for tool_call in last_message.tool_calls:
                        if hasattr(tool_call, 'args'):
                            items = extract_actionable_items_from_tool_response(tool_call.args)
                            # Filter for integration-related items
                            for item in items:
                                # Look for keywords that suggest integration/synergy
                                item_text = f"{item.get('title', '')} {item.get('description', '')} {item.get('labels', '')}".lower()
                                if any(keyword in item_text for keyword in ['integration', 'workflow', 'automation', 'devops', 'ci/cd', 'microservices', 'polyglot']):
                                    integration_examples.append(item)
            
            return {
                "github_links": github_links,
                "integration_examples": integration_examples
            }

        def synthesize_node(state: State, config: RunnableConfig) -> State:
            """Synthesize findings into a comprehensive summary with actual GitHub links"""
            subscription_key = os.getenv("AZURE_OPENAI_API_KEY")
            api_version = "2024-12-01-preview"
            llm = AzureChatOpenAI(
                api_key=subscription_key,
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_version=api_version,
                deployment_name="gpt-4o-mini"
            )
            
            github_links_markdown = format_github_links_for_markdown(
                state.get("github_links", []), 
                "🔗 Synergistic Integration Resources"
            )
            
            # Format integration examples
            integration_examples_text = ""
            if state.get("integration_examples"):
                integration_examples_text = "\n### 🔄 Integration Success Stories\n\n"
                for example in state["integration_examples"][:8]:  # Limit to top 8
                    integration_examples_text += f"- **{example.get('title', 'Unknown')}**\n"
                    integration_examples_text += f"  - Type: {example.get('type', 'Unknown')}\n"
                    integration_examples_text += f"  - URL: {example.get('url', 'N/A')}\n"
                    integration_examples_text += f"  - Labels: {example.get('labels', 'None')}\n"
                    integration_examples_text += f"  - Summary: {example.get('description', 'No description')}\n\n"
            
            synthesis_prompt = f"""Based on the research conducted, create a comprehensive markdown summary focused on Habit 6 - Synergize integration patterns and multi-tool collaboration.

Structure the summary as follows:

# Habit 6 - Synergize: Multi-tool & Repository Integration

**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 🔄 Focus: Creating Synergistic Value Through Integration

### Overview
Summarize the key findings related to multi-tool integration patterns, cross-functional collaboration, and synergistic workflows that create value greater than the sum of parts.

### Multi-Tool Integration Champions
[List repositories that excel at integrating multiple development tools seamlessly]

### Cross-Functional Collaboration Examples
[Document projects that show excellent collaboration across different domains and skill sets]

### Workflow Synergies That Amplify Productivity
[Highlight specific workflows and tool chains that create multiplicative value]

{integration_examples_text}

{github_links_markdown}

## 🛠️ Tool Chain Patterns That Work
[Document specific combinations of tools that work better together than separately]

### CI/CD Integration Excellence
[Showcase repositories with outstanding continuous integration and deployment workflows]

### Polyglot Project Success Stories
[Highlight projects that successfully combine multiple programming languages]

### Automation That Enables Teams
[Document automation patterns that amplify team effectiveness]

## 🚀 Action Items for Better Integration

### This Week
1. [Specific tool integration to implement]
2. [Workflow improvement to try]
3. [Cross-functional collaboration to start]

### This Month
1. [Integration project to pursue]
2. [Tool chain to optimize]
3. [Automation to build]

---

Focus on concrete examples and actionable patterns that create synergistic value through effective tool and team integration.
"""
            
            synthesis_message = SystemMessage(content=synthesis_prompt)
            ai: AIMessage = llm.invoke(state["messages"] + [synthesis_message], config=config)
            return {
                "messages": [ai],
                "summary": ai.content
            }

        def save_summary_node(state: State, config: RunnableConfig) -> State:
            summary = state.get("summary", "")
            output_path = os.path.join("data", "habits", "habit6_synergize.md")
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(summary)
            return state

        # ToolNode handles tool calls
        tool_node = ToolNode(tools=github_tools)

        # Build the graph
        graph = StateGraph(State)
        graph.add_node("collect_data", data_collection_node)
        graph.add_node("tools", tool_node)
        graph.add_node("extract_links", link_extraction_node)
        graph.add_node("synthesize", synthesize_node)
        graph.add_node("save", save_summary_node)
        
        graph.add_edge(START, "collect_data")
        graph.add_edge("collect_data", "tools")
        graph.add_edge("tools", "extract_links")
        graph.add_edge("extract_links", "synthesize")
        graph.add_edge("synthesize", "save")
        graph.add_edge("save", END)
        
        return graph
    except Exception as e:
        log(f"Error building habit6-synergize graph: {e}")
        return None