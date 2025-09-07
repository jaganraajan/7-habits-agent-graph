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
PROMPT_KEY = "habit4_win_win"

# the state that will be passed to each node
class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    github_links: list[str]
    actionable_items: list[dict]
    summary: str

def init_state() -> State:
    system_prompt = get_prompt(PROMPT_KEY) or """You are a collaborative GitHub research assistant focused on Win-Win development patterns and MCP Evaluation Framework opportunities.

Your mission is to find actionable issues and collaborative work specifically related to building evaluation frameworks for Model Context Protocol (MCP) that would help AI optimize software for companies.

Focus areas:
1. MCP evaluation framework development opportunities
2. Testing and benchmarking frameworks for AI tools
3. Collaborative issues involving multiple stakeholders
4. Win-win scenarios in open source projects
5. Consensus-building patterns in development teams

Target repositories and issues that involve:
- MCP protocol testing and evaluation
- AI software optimization frameworks
- Multi-party collaboration on technical standards
- Evaluation metrics for AI-powered tools
- Open source governance and consensus building"""
    
    return {
        "messages": [SystemMessage(content=system_prompt)],
        "github_links": [],
        "actionable_items": [],
        "summary": ""
    }

@registered_graph("habit4-win-win")
def build_graph() -> StateGraph:
    load_dotenv()
    try:
        github_tools = get_mcp_tools("github")

        def data_collection_node(state: State, config: RunnableConfig) -> State:
            """Collect data focused on MCP evaluation framework and collaborative development"""
            subscription_key = os.getenv("AZURE_OPENAI_API_KEY")
            api_version = "2024-12-01-preview"
            llm = AzureChatOpenAI(
                api_key=subscription_key,
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_version=api_version,
                deployment_name="gpt-4o-mini"
            ).bind_tools(github_tools)
            
            research_prompt = """
Search for repositories and issues specifically related to MCP (Model Context Protocol) evaluation frameworks and collaborative development patterns.

PRIORITY SEARCH TARGETS:
1. Search for "MCP evaluation" OR "model context protocol testing" OR "MCP benchmark"
2. Search for issues labeled "evaluation", "framework", "testing", "collaboration"
3. Look for repositories with "mcp" OR "model-context-protocol" in name/description
4. Find issues with multiple assignees or collaborative discussions
5. Search for "win-win", "consensus", "stakeholder" in issue discussions

Use these specific search queries:
- search_repositories: query="MCP evaluation framework" OR "model context protocol testing"
- search_issues: query="label:evaluation framework" OR "label:testing mcp"
- search_code: query="evaluation framework language:python"
- search_repositories: query="topic:mcp OR topic:model-context-protocol"

Focus on finding actionable issues that would help AI optimize software for companies through better evaluation frameworks.
"""
            
            research_message = SystemMessage(content=research_prompt)
            ai: AIMessage = llm.invoke(state["messages"] + [research_message], config=config)
            return {"messages": [ai]}

        def link_extraction_node(state: State, config: RunnableConfig) -> State:
            """Extract GitHub links and actionable items from tool responses"""
            # Extract links from all messages
            github_links = extract_github_links_from_messages(state["messages"])
            
            # Extract actionable items from the latest AI message if it has tool calls
            actionable_items = []
            if state["messages"]:
                last_message = state["messages"][-1]
                if isinstance(last_message, AIMessage) and hasattr(last_message, 'tool_calls'):
                    for tool_call in last_message.tool_calls:
                        if hasattr(tool_call, 'args'):
                            items = extract_actionable_items_from_tool_response(tool_call.args)
                            actionable_items.extend(items)
            
            return {
                "github_links": github_links,
                "actionable_items": actionable_items
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
            
            # Format GitHub links for inclusion in summary
            github_links_markdown = format_github_links_for_markdown(
                state.get("github_links", []), 
                "🔗 MCP Evaluation Framework Resources"
            )
            
            # Format actionable items
            actionable_items_text = ""
            if state.get("actionable_items"):
                actionable_items_text = "\n### 🎯 Actionable Opportunities\n\n"
                for item in state["actionable_items"][:10]:  # Limit to top 10
                    actionable_items_text += f"- **{item.get('title', 'Unknown')}** ({item.get('type', 'Unknown')})\n"
                    actionable_items_text += f"  - URL: {item.get('url', 'N/A')}\n"
                    actionable_items_text += f"  - Status: {item.get('state', 'unknown')}\n"
                    if item.get('labels'):
                        actionable_items_text += f"  - Labels: {item.get('labels')}\n"
                    actionable_items_text += f"  - Description: {item.get('description', 'No description')}\n\n"
            
            synthesis_prompt = f"""Based on the research conducted, create a comprehensive markdown summary focused on Habit 4 - Win-Win collaborative development patterns and MCP evaluation framework opportunities.

Structure the summary as follows:

# Habit 4 - Win-Win: MCP Evaluation Framework & Collaborative Development

**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 🎯 Focus: Building MCP Evaluation Frameworks for AI Optimization

### Overview
Summarize the key findings related to MCP evaluation frameworks and collaborative development opportunities that would help AI optimize software for companies.

### Top MCP Evaluation Framework Opportunities
[List specific repositories and issues focused on MCP evaluation, testing, and benchmarking]

### Collaborative Development Patterns
[Document examples of win-win collaboration in MCP and AI tooling projects]

### Consensus Building in Technical Standards
[Highlight examples of effective consensus-building in MCP or similar protocol development]

{actionable_items_text}

{github_links_markdown}

## 🚀 Immediate Action Items for MCP Evaluation Framework Development

### This Week
1. [Specific action related to MCP evaluation framework]
2. [Specific collaborative opportunity identified]
3. [Specific issue to contribute to]

### This Month
1. [Medium-term goal for MCP evaluation work]
2. [Collaboration opportunity to pursue]
3. [Framework component to develop]

---

Focus on concrete, actionable opportunities that promote win-win collaboration while advancing MCP evaluation capabilities for AI-powered software optimization.
"""
            
            synthesis_message = SystemMessage(content=synthesis_prompt)
            ai: AIMessage = llm.invoke(state["messages"] + [synthesis_message], config=config)
            return {
                "messages": [ai],
                "summary": ai.content
            }

        def save_summary_node(state: State, config: RunnableConfig) -> State:
            summary = state.get("summary", "")
            output_path = os.path.join("data", "habits", "habit4_win_win.md")
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
        log(f"Error building habit4-win-win graph: {e}")
        return None