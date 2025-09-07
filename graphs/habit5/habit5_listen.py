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
PROMPT_KEY = "habit5_listen"

# the state that will be passed to each node
class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    github_links: list[str]
    listening_examples: list[dict]
    summary: str

def init_state() -> State:
    system_prompt = get_prompt(PROMPT_KEY) or """You are a GitHub research assistant focused on best practices for listening, understanding, and thoughtful review in LLMs, agentic AI, and advanced AI projects.\n\nYour mission is to find excellent examples of repositories and projects that demonstrate active listening, deep understanding, and high-quality review/discussion in the context of LLMs, agentic AI, and autonomous agent systems.\n\nFocus areas:\n1. Thoughtful code review discussions in LLM/agentic AI projects\n2. ADR (Architecture Decision Records), RFC (Request for Comments), and design discussion processes\n3. Projects that emphasize understanding-first approaches in AI/LLM/agentic development\n4. Learning from disagreements and collaborative problem solving in AI/LLM/agentic communities\n5. Documentation and communication patterns that foster deep understanding\n\nLook for patterns where projects:\n- Have detailed, respectful, and constructive review discussions\n- Use ADRs, RFCs, or similar processes for major decisions\n- Encourage contributors to seek first to understand before proposing changes\n- Document disagreements and their resolutions for learning\n- Foster a culture of listening and understanding in AI/LLM/agentic teams"""
    return {
        "messages": [SystemMessage(content=system_prompt)],
        "github_links": [],
        "listening_examples": [],
        "summary": ""
    }

@registered_graph("habit5-listen")
def build_graph() -> StateGraph:
    load_dotenv()
    try:
        github_tools = get_mcp_tools("github")

        def data_collection_node(state: State, config: RunnableConfig) -> State:
            """Collect data focused on listening, understanding, and review best practices"""
            subscription_key = os.getenv("AZURE_OPENAI_API_KEY")
            api_version = "2024-12-01-preview"
            llm = AzureChatOpenAI(
                api_key=subscription_key,
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_version=api_version,
                deployment_name="gpt-4o-mini"
            ).bind_tools(github_tools)
            
            research_prompt = """
Search for repositories and projects that demonstrate best practices in listening, understanding, and thoughtful review in LLMs, agentic AI, and advanced AI systems.

SEARCH TARGETS:
1. Look for repositories with detailed, respectful, and constructive code review discussions in LLM/agentic AI projects
2. Search for projects that use ADRs, RFCs, or similar processes for major decisions in AI/LLM/agentic development
3. Find repositories that emphasize understanding-first approaches and collaborative problem solving
4. Look for documentation and communication patterns that foster deep understanding in AI/LLM/agentic teams
5. Search for projects that document disagreements and their resolutions for learning

Use these specific search queries:
- search_issues: query="review OR discussion OR ADR OR RFC OR understanding OR disagreement topic:llm OR topic:agentic-ai OR topic:autonomous-agents"
- search_repositories: query="llm OR agentic OR autonomous OR langchain OR openai OR gpt OR llama OR transformers OR ai OR review OR RFC OR ADR"
- search_code: query="ADR OR RFC OR review OR discussion"
- get_file_contents: Look for ADR.md, RFC.md, docs/ directories, review/discussion threads
- search_repositories: query="topic:review OR topic:discussion OR topic:adr OR topic:rfc OR topic:understanding"

Focus on finding examples where listening, understanding, and thoughtful review are core to the project's culture and process.
"""
            research_message = SystemMessage(content=research_prompt)
            ai: AIMessage = llm.invoke(state["messages"] + [research_message], config=config)
            return {"messages": [ai]}

        def link_extraction_node(state: State, config: RunnableConfig) -> State:
            """Extract GitHub links and listening/review examples from tool responses"""
            github_links = extract_github_links_from_messages(state["messages"])
            
            # Extract listening/review examples
            listening_examples = []
            if state["messages"]:
                last_message = state["messages"][-1]
                if isinstance(last_message, AIMessage) and hasattr(last_message, 'tool_calls'):
                    for tool_call in last_message.tool_calls:
                        if hasattr(tool_call, 'args'):
                            items = extract_actionable_items_from_tool_response(tool_call.args)
                            # Filter for listening/review-related items
                            for item in items:
                                item_text = f"{item.get('title', '')} {item.get('description', '')} {item.get('labels', '')}".lower()
                                if any(keyword in item_text for keyword in [
                                    'review', 'discussion', 'adr', 'rfc', 'understanding', 'disagreement', 'listening', 'collaborative', 'problem solving',
                                    'llm', 'agentic', 'autonomous', 'langchain', 'openai', 'gpt', 'llama', 'transformers', 'ai']):
                                    listening_examples.append(item)
            return {
                "github_links": github_links,
                "listening_examples": listening_examples
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
                "🔗 Listening & Review Best Practices"
            )
            
            # Format listening/review examples
            listening_examples_text = ""
            if state.get("listening_examples"):
                listening_examples_text = "\n### 👂 Listening & Review Success Stories\n\n"
                for example in state["listening_examples"][:8]:  # Limit to top 8
                    listening_examples_text += f"- **{example.get('title', 'Unknown')}**\n"
                    listening_examples_text += f"  - Type: {example.get('type', 'Unknown')}\n"
                    listening_examples_text += f"  - URL: {example.get('url', 'N/A')}\n"
                    listening_examples_text += f"  - Labels: {example.get('labels', 'None')}\n"
                    listening_examples_text += f"  - Summary: {example.get('description', 'No description')}\n\n"
            
            synthesis_prompt = f"""Based on the research conducted, create a comprehensive markdown summary focused on Habit 5 - Seek First to Understand, with a special emphasis on listening, understanding, and thoughtful review in LLMs, agentic AI, and advanced AI systems.\n\nStructure the summary as follows:\n\n# Habit 5 - Seek First to Understand: Listening, Review & Understanding in LLMs/Agentic AI\n\n**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n## 👂 Focus: Listening, Understanding, and Thoughtful Review in LLMs/Agentic AI\n\n### Overview\nSummarize the key findings related to listening, understanding, and review best practices in LLM/agentic/AI projects.\n\n### Review & Discussion Champions\n[List repositories that excel at review, discussion, and understanding-first approaches in LLM/agentic AI]\n\n### ADR, RFC, and Design Decision Excellence\n[Document projects that use ADRs, RFCs, or similar processes for major decisions in LLM/agentic AI]\n\n### Collaborative Problem Solving & Disagreement Resolution\n[Highlight projects that foster learning from disagreements and collaborative problem solving in LLM/agentic AI communities]\n\n{listening_examples_text}\n\n{github_links_markdown}\n\n## 📝 Documentation & Communication Patterns\n[Document patterns that foster deep understanding and effective communication in LLM/agentic AI projects]\n\n### Action Items for Better Listening & Understanding\n\n#### This Week\n1. [Review a major PR or RFC in an LLM/agentic AI project]\n2. [Participate in a design discussion or ADR process]\n3. [Document a disagreement and its resolution]\n\n#### This Month\n1. [Contribute to a project with a strong review culture]\n2. [Propose an ADR or RFC in an LLM/agentic AI repo]\n3. [Share a lesson learned from a disagreement]\n\n---\n\nFocus on concrete examples and actionable patterns that foster listening, understanding, and thoughtful review in LLMs, agentic AI, and advanced AI systems.\n"""
            synthesis_message = SystemMessage(content=synthesis_prompt)
            ai: AIMessage = llm.invoke(state["messages"] + [synthesis_message], config=config)
            return {
                "messages": [ai],
                "summary": ai.content
            }

        def save_summary_node(state: State, config: RunnableConfig) -> State:
            summary = state.get("summary", "")
            output_path = os.path.join("data", "habits", "habit5_listen.md")
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
        log(f"Error building habit5-listen graph: {e}")
        return None
