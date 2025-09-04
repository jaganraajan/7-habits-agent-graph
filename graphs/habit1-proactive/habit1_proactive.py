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

PROMPT_KEY = "habit1_proactive"

class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    summary: str

def init_state() -> State:
    system_prompt = """
        You are a proactive GitHub research assistant for the 7 Habits Agent Graph.

        Your mission:
        - Research agentic/MCP repositories using the available GitHub tools.
        - Find top agentic/MCP repositories for potential contributions.
        - Identify beginner-friendly issues (good first issue, help wanted).
        - Look for ROADMAP, ADR, and CONTRIBUTING documentation.
        - Find example agentic patterns and recent changelogs.
        - Summarize findings in a clear, actionable format.

        **Instructions:**
        - You MUST use the available GitHub tools (search_repositories, search_code, search_issues, get_file_contents) to gather information.
        - Do NOT answer with a summary until you have called the tools and received results.
        - After each tool call, review the results and decide if more information is needed.
        - When you have gathered enough data, reply: "Ready to synthesize."
        - You may loop up to 3 times to gather information before synthesizing.
        """
    return {
        "messages": [SystemMessage(content=system_prompt)],
        "summary": ""
    }

@registered_graph("habit1-proactive")
def build_graph() -> StateGraph:
    load_dotenv()
    try:
        github_tools = get_mcp_tools("github")

        MAX_ITER = 3  # Maximum number of research-tool loops

        def research_node(state: State, config: RunnableConfig) -> State:
            # Track loop count in state
            state["loop_count"] = state.get("loop_count", 0) + 1
            subscription_key = os.getenv("AZURE_OPENAI_API_KEY")
            api_version = "2024-12-01-preview"
            llm = AzureChatOpenAI(
                api_key=subscription_key,
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_version=api_version,
                deployment_name="gpt-4o-mini"
            )
            research_prompt = """
Research agentic/MCP repositories and gather:
- Top repositories (using search_repositories)
- Beginner-friendly issues (using search_issues)
- Documentation files (using get_file_contents)
- Recent changelogs and patterns

Use the available tools to collect this information. When you have enough, let me know you're ready to synthesize.
"""
            research_message = SystemMessage(content=research_prompt)
            ai: AIMessage = llm.invoke(state["messages"] + [research_message], config=config)
            return {"messages": [ai], "loop_count": state["loop_count"]}

        def should_continue_tooluse(state: State, config: RunnableConfig) -> str:
            # If loop count exceeded, go to synthesize
            if state.get("loop_count", 0) >= MAX_ITER:
                return "synthesize"
            # If the last message says ready to synthesize, move on
            last_msg = state["messages"][-1]
            if hasattr(last_msg, "content") and "ready to synthesize" in last_msg.content.lower():
                return "synthesize"
            return "research"

        def synthesize_node(state: State, config: RunnableConfig) -> State:
            """LLM synthesizes research results into a summary."""
            subscription_key = os.getenv("AZURE_OPENAI_API_KEY")
            api_version = "2024-12-01-preview"
            llm = AzureChatOpenAI(
                api_key=subscription_key,
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_version=api_version,
                deployment_name="gpt-4o-mini"
            )
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
            summary = state.get("summary", "")
            output_path = os.path.join("data", "habits", "habit1_proactive_summary.md")
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(summary)
            return state

        tool_node = ToolNode(tools=github_tools)

        graph = StateGraph(State)
        graph.add_node("research", research_node)
        graph.add_node("tools", tool_node)
        graph.add_node("synthesize", synthesize_node)
        graph.add_node("save", save_summary_node)
        graph.add_edge(START, "research")
        graph.add_edge("research", "tools")
        graph.add_conditional_edges(
            "tools",
            should_continue_tooluse,
            {
                "research": "research",
                "synthesize": "synthesize"
            }
        )
        graph.add_edge("synthesize", "save")
        graph.add_edge("save", END)
        return graph
    except Exception as e:
        log(f"Error building habit1-proactive graph: {e}")
        return None