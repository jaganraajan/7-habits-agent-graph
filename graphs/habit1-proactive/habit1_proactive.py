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

# this is the key for the prompt in the prompt manager which gets the Langfuse prompt
PROMPT_KEY = "habit1_proactive"

# the state that will be passed to each node
class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    github_results: dict
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
        "github_results": {},
        "summary": ""
    }

@registered_graph("habit1-proactive")
def build_graph() -> StateGraph:
    load_dotenv()
    try:
        # Get MCP tools
        github_tools = get_mcp_tools("github")
        filesystem_tools = get_mcp_tools("filesystem") 
        todo_tools = get_mcp_tools("todo")
        
        # Combine all tools
        all_tools = [
            *github_tools,
            *filesystem_tools,
            *todo_tools
        ]
        
        def research_node(state: State, config: RunnableConfig) -> State:
            """Research GitHub repositories for agentic/MCP content"""
            subscription_key = os.getenv("AZURE_OPENAI_API_KEY")
            api_version = "2024-12-01-preview"

            # Initialize LLM with tools
            llm = AzureChatOpenAI(
                api_key=subscription_key,
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_version=api_version,
                deployment_name="gpt-4o-mini"
            ).bind_tools(github_tools)
            
            # Create research prompt
            research_prompt = """
Search for and analyze repositories related to:
1. Agent frameworks (LangGraph, CrewAI, AutoGen, etc.)
2. MCP (Model Context Protocol) implementations 
3. Agentic AI patterns and examples
4. AI assistant/agent repositories

For each relevant repository found:
- Look for beginner-friendly issues (good first issue, help wanted labels)
- Find documentation (ROADMAP.md, ADR/, CONTRIBUTING.md)
- Check recent changelogs and patterns
- Note contribution opportunities

Use the search_repositories and search_code tools to find relevant repositories.
Use search_issues to find beginner-friendly issues.
Use get_file_contents to examine documentation files.
"""
            
            # Add research prompt to messages
            research_message = SystemMessage(content=research_prompt)
            ai: AIMessage = llm.invoke(state["messages"] + [research_message], config=config)
            
            return {"messages": [ai]}

        def synthesize_node(state: State, config: RunnableConfig) -> State:
            """Synthesize research results into a summary"""
            subscription_key = os.getenv("AZURE_OPENAI_API_KEY")
            api_version = "2024-12-01-preview"

            # Initialize LLM without tools for summary generation
            llm = AzureChatOpenAI(
                api_key=subscription_key,
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_version=api_version,
                deployment_name="gpt-4o-mini"
            )
            
            # Create synthesis prompt
            synthesis_prompt = f"""Based on the research conducted, create a comprehensive markdown summary for Habit 1 - Be Proactive.

Structure the summary as follows:

# Habit 1 - Be Proactive: Weekly GitHub Research Summary

**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 🎯 Top Agentic/MCP Repositories for Contribution

[List the most promising repositories found with brief descriptions]

## 🌱 Beginner-Friendly Opportunities  

[List good first issues and help wanted items with links]

## 📚 Learning Resources

[Document any ROADMAP, ADR, CONTRIBUTING guides found]

## 🔍 Recent Patterns & Examples

[Highlight interesting agentic patterns and recent developments]

## ⚡ Top 3 Action Items

[3 specific, actionable next steps for learning/contributing]

---

Make this practical and actionable. Focus on concrete opportunities for skill development and contribution.
"""
            
            synthesis_message = SystemMessage(content=synthesis_prompt)
            ai: AIMessage = llm.invoke(state["messages"] + [synthesis_message], config=config)
            
            return {
                "messages": [ai],
                "summary": ai.content
            }

        def save_summary_node(state: State, config: RunnableConfig) -> State:
            """Save the summary to markdown file using Filesystem MCP"""
            subscription_key = os.getenv("AZURE_OPENAI_API_KEY")
            api_version = "2024-12-01-preview"

            # Initialize LLM with filesystem tools
            llm = AzureChatOpenAI(
                api_key=subscription_key,
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_version=api_version,
                deployment_name="gpt-4o-mini"
            ).bind_tools(filesystem_tools)
            
            # Create save prompt
            save_prompt = f"""Save the following content to the file 'data/habits/habit1_proactive_summary.md':

{state['summary']}

Use the write_file tool to save this content. Make sure the directory structure exists."""
            
            save_message = SystemMessage(content=save_prompt)
            ai: AIMessage = llm.invoke([save_message], config=config)
            
            return {"messages": [ai]}

        def add_todos_node(state: State, config: RunnableConfig) -> State:
            """Optionally add top 3 action items to TODO list"""
            if not todo_tools:
                log("TODO tools not available, skipping TODO creation")
                return {"messages": [AIMessage(content="TODO integration not available")]}
                
            subscription_key = os.getenv("AZURE_OPENAI_API_KEY")
            api_version = "2024-12-01-preview"

            # Initialize LLM with TODO tools
            llm = AzureChatOpenAI(
                api_key=subscription_key,
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_version=api_version,
                deployment_name="gpt-4o-mini"
            ).bind_tools(todo_tools)
            
            # Create TODO prompt
            todo_prompt = f"""Extract the top 3 action items from this summary and add them to the TODO list:

{state['summary']}

Create specific, actionable TODO items with appropriate priorities. Use the add_todo_prompt tool for each item."""
            
            todo_message = SystemMessage(content=todo_prompt)
            ai: AIMessage = llm.invoke([todo_message], config=config)
            
            return {"messages": [ai]}

        # Create tool node for all tools
        tool_node = ToolNode(all_tools)
        
        # Router functions
        def should_call_tool(state: State) -> str:
            last_message = state["messages"][-1]
            if getattr(last_message, "tool_calls", None):
                return "tools"
            else:
                # Check which stage we're in based on message content
                content = last_message.content.lower()
                if "research" in content or len(state["messages"]) <= 2:
                    return "synthesize"
                elif "summary" in content or state.get("summary"):
                    return "save"
                else:
                    return "todos"

        def after_save_routing(state: State) -> str:
            # After saving, optionally add to TODO list
            return "todos"

        # Build the graph
        graph = StateGraph(State)
        
        # Add nodes
        graph.add_node("research", research_node)
        graph.add_node("tools", tool_node)
        graph.add_node("synthesize", synthesize_node)
        graph.add_node("save", save_summary_node)
        graph.add_node("todos", add_todos_node)
        
        # Add edges
        graph.add_edge(START, "research")
        graph.add_conditional_edges("research", should_call_tool, {
            "tools": "tools",
            "synthesize": "synthesize"
        })
        graph.add_edge("tools", "research")  # Loop back for more tool usage
        graph.add_edge("synthesize", "save")
        graph.add_conditional_edges("save", should_call_tool, {
            "tools": "tools",
            "todos": "todos"
        })
        graph.add_conditional_edges("todos", should_call_tool, {
            "tools": "tools",
            "end": END
        })
        graph.add_edge("todos", END)
        
        return graph
        
    except Exception as e:
        log(f"Error building habit1-proactive graph: {e}")
        return None