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
PROMPT_KEY = "habit4_winwin"

# the state that will be passed to each node
class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    github_links: list[str]
    winwin_examples: list[dict]
    summary: str

def init_state() -> State:
    system_prompt = get_prompt(PROMPT_KEY) or """You are a GitHub research assistant focused on win-win collaboration, mutual benefit, and positive-sum patterns in LLMs, agentic AI, and advanced AI projects.\n\nYour mission is to find excellent examples of repositories and projects that demonstrate collaborative development, mutual benefit, and win-win approaches in the context of LLMs, agentic AI, and autonomous agent systems.\n\nFocus areas:\n1. Collaborative issue resolution and PRs in LLM/agentic AI projects\n2. Mutual benefit code reviews and consensus building\n3. Projects that foster team synergy and positive-sum outcomes\n4. Patterns of shared learning, resource sharing, and open collaboration\n5. Documentation and communication that highlight win-win solutions\n\nLook for patterns where projects:\n- Encourage collaboration and shared success\n- Foster mutual benefit in code review and decision making\n- Build consensus and resolve conflicts constructively\n- Share resources, knowledge, and learning openly\n- Demonstrate positive-sum outcomes in AI/LLM/agentic teams"""
    return {
        "messages": [SystemMessage(content=system_prompt)],
        "github_links": [],
        "winwin_examples": [],
        "summary": ""
    }

@registered_graph("habit4-winwin")
def build_graph() -> StateGraph:
    load_dotenv()
    try:
        github_tools = get_mcp_tools("github")

        def data_collection_node(state: State, config: RunnableConfig) -> State:
            """Collect data focused on win-win collaboration and mutual benefit"""
            subscription_key = os.getenv("AZURE_OPENAI_API_KEY")
            api_version = "2024-12-01-preview"
            llm = AzureChatOpenAI(
                api_key=subscription_key,
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_version=api_version,
                deployment_name="gpt-4o-mini"
            ).bind_tools(github_tools)
            
            research_prompt = """
Search for repositories and projects that demonstrate win-win collaboration, mutual benefit, and positive-sum patterns in LLMs, agentic AI, and advanced AI systems.

SEARCH TARGETS:
1. Look for repositories with collaborative issue resolution and PRs in LLM/agentic AI projects
2. Search for projects that foster mutual benefit in code reviews and consensus building
3. Find repositories that encourage team synergy and positive-sum outcomes
4. Look for documentation and communication that highlight win-win solutions
5. Search for patterns of shared learning, resource sharing, and open collaboration

Use these specific search queries:
- search_issues: query="collaboration OR consensus OR win-win OR mutual benefit OR synergy topic:llm OR topic:agentic-ai OR topic:autonomous-agents"
- search_repositories: query="llm OR agentic OR autonomous OR langchain OR openai OR gpt OR llama OR transformers OR ai OR collaboration OR win-win OR synergy"
- search_code: query="collaboration OR consensus OR win-win OR mutual benefit OR synergy"
- get_file_contents: Look for COLLABORATION.md, SYNERGY.md, docs/ directories, PR/issue threads
- search_repositories: query="topic:collaboration OR topic:win-win OR topic:synergy OR topic:mutual-benefit"

Focus on finding examples where collaboration, mutual benefit, and win-win outcomes are core to the project's culture and process.
"""
            research_message = SystemMessage(content=research_prompt)
            ai: AIMessage = llm.invoke(state["messages"] + [research_message], config=config)
            return {"messages": [ai]}

        def link_extraction_node(state: State, config: RunnableConfig) -> State:
            """Extract GitHub links and win-win collaboration examples from tool responses"""
            github_links = extract_github_links_from_messages(state["messages"])
            
            # Extract win-win collaboration examples
            winwin_examples = []
            if state["messages"]:
                last_message = state["messages"][-1]
                if isinstance(last_message, AIMessage) and hasattr(last_message, 'tool_calls'):
                    for tool_call in last_message.tool_calls:
                        if hasattr(tool_call, 'args'):
                            items = extract_actionable_items_from_tool_response(tool_call.args)
                            # Filter for win-win/collaboration-related items
                            for item in items:
                                item_text = f"{item.get('title', '')} {item.get('description', '')} {item.get('labels', '')}".lower()
                                if any(keyword in item_text for keyword in [
                                    'collaboration', 'consensus', 'win-win', 'mutual benefit', 'synergy', 'shared', 'open', 'team',
                                    'llm', 'agentic', 'autonomous', 'langchain', 'openai', 'gpt', 'llama', 'transformers', 'ai']):
                                    winwin_examples.append(item)
            return {
                "github_links": github_links,
                "winwin_examples": winwin_examples
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
                "🔗 Win-Win Collaboration Resources"
            )
            
            # Format win-win collaboration examples
            winwin_examples_text = ""
            if state.get("winwin_examples"):
                winwin_examples_text = "\n### 🤝 Win-Win Collaboration Success Stories\n\n"
                for example in state["winwin_examples"][:8]:  # Limit to top 8
                    winwin_examples_text += f"- **{example.get('title', 'Unknown')}**\n"
                    winwin_examples_text += f"  - Type: {example.get('type', 'Unknown')}\n"
                    winwin_examples_text += f"  - URL: {example.get('url', 'N/A')}\n"
                    winwin_examples_text += f"  - Labels: {example.get('labels', 'None')}\n"
                    winwin_examples_text += f"  - Summary: {example.get('description', 'No description')}\n\n"
            
            synthesis_prompt = f"""Based on the research conducted, create a comprehensive markdown summary focused on Habit 4 - Think Win-Win, with a special emphasis on collaboration, mutual benefit, and positive-sum patterns in LLMs, agentic AI, and advanced AI systems.\n\nStructure the summary as follows:\n\n# Habit 4 - Think Win-Win: Collaboration & Mutual Benefit in LLMs/Agentic AI\n\n**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n## 🤝 Focus: Collaboration, Mutual Benefit, and Win-Win Outcomes in LLMs/Agentic AI\n\n### Overview\nSummarize the key findings related to collaboration, mutual benefit, and win-win patterns in LLM/agentic/AI projects.\n\n### Collaboration & Consensus Champions\n[List repositories that excel at collaborative issue resolution, PRs, and consensus building in LLM/agentic AI]\n\n### Mutual Benefit & Synergy Examples\n[Document projects that foster mutual benefit, team synergy, and positive-sum outcomes in LLM/agentic AI]\n\n### Shared Learning & Open Collaboration\n[Highlight projects that encourage shared learning, resource sharing, and open collaboration in LLM/agentic AI communities]\n\n{winwin_examples_text}\n\n{github_links_markdown}\n\n## 📖 Documentation & Communication Patterns\n[Document patterns that highlight win-win solutions and positive-sum outcomes in LLM/agentic AI projects]\n\n### Action Items for Better Collaboration & Mutual Benefit\n\n#### This Week\n1. [Collaborate on an issue or PR in an LLM/agentic AI project]\n2. [Participate in a consensus-building discussion]\n3. [Share a resource or learning with the community]\n\n#### This Month\n1. [Contribute to a project with a strong collaboration culture]\n2. [Propose a win-win solution in an LLM/agentic AI repo]\n3. [Document a positive-sum outcome or shared success]\n\n---\n\nFocus on concrete examples and actionable patterns that foster collaboration, mutual benefit, and win-win outcomes in LLMs, agentic AI, and advanced AI systems.\n"""
            synthesis_message = SystemMessage(content=synthesis_prompt)
            ai: AIMessage = llm.invoke(state["messages"] + [synthesis_message], config=config)
            return {
                "messages": [ai],
                "summary": ai.content
            }

        def save_summary_node(state: State, config: RunnableConfig) -> State:
            summary = state.get("summary", "")
            output_path = os.path.join("data", "habits", "habit4_summary.md")
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
        log(f"Error building habit4-winwin graph: {e}")
        return None
