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
PROMPT_KEY = "habit5_understand"

# the state that will be passed to each node
class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    github_links: list[str]
    discussion_examples: list[dict]
    summary: str

def init_state() -> State:
    system_prompt = get_prompt(PROMPT_KEY) or """You are a GitHub research assistant focused on understanding-first communication patterns in code reviews and technical discussions.

Your mission is to find excellent examples of thoughtful discussion, deep listening, and understanding-first approaches in GitHub repositories.

Focus areas:
1. Code review discussions that show empathy and understanding
2. Architecture Decision Records (ADRs) and RFC processes
3. Issue discussions with thoughtful disagreement resolution
4. Documentation that demonstrates deep listening
5. Examples of teams seeking understanding before being understood

Look for patterns where teams:
- Ask clarifying questions before proposing solutions
- Acknowledge different perspectives before debating
- Use inclusive language and seek consensus
- Document reasoning and decision-making processes
- Show evidence of learning from diverse viewpoints"""
    
    return {
        "messages": [SystemMessage(content=system_prompt)],
        "github_links": [],
        "discussion_examples": [],
        "summary": ""
    }

@registered_graph("habit5-understand")
def build_graph() -> StateGraph:
    load_dotenv()
    try:
        github_tools = get_mcp_tools("github")

        def data_collection_node(state: State, config: RunnableConfig) -> State:
            """Collect data focused on understanding-first communication patterns"""
            subscription_key = os.getenv("AZURE_OPENAI_API_KEY")
            api_version = "2024-12-01-preview"
            llm = AzureChatOpenAI(
                api_key=subscription_key,
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_version=api_version,
                deployment_name="gpt-4o-mini"
            ).bind_tools(github_tools)
            
            research_prompt = """
Search for repositories and discussions that demonstrate excellent understanding-first communication patterns.

SEARCH TARGETS:
1. Look for repositories with extensive ADR (Architecture Decision Records) folders
2. Search for pull requests with thoughtful review discussions
3. Find issues with labels like "discussion", "rfc", "proposal", "design"
4. Look for repositories with CONTRIBUTING.md that emphasize understanding and empathy
5. Search for code review templates that promote understanding

Use these specific search queries:
- search_repositories: query="ADR OR architecture-decision-records"
- search_issues: query="label:discussion OR label:rfc thoughtful"
- search_code: query="RFC OR 'request for comments' language:markdown"
- get_file_contents: Look for CONTRIBUTING.md, CODE_OF_CONDUCT.md, RFC/ directories
- search_pull_requests: Look for PRs with extensive review discussions

Focus on finding examples where teams practice deep listening and seek understanding first.
"""
            
            research_message = SystemMessage(content=research_prompt)
            ai: AIMessage = llm.invoke(state["messages"] + [research_message], config=config)
            return {"messages": [ai]}

        def link_extraction_node(state: State, config: RunnableConfig) -> State:
            """Extract GitHub links and discussion examples from tool responses"""
            github_links = extract_github_links_from_messages(state["messages"])
            
            # Extract discussion examples
            discussion_examples = []
            if state["messages"]:
                last_message = state["messages"][-1]
                if isinstance(last_message, AIMessage) and hasattr(last_message, 'tool_calls'):
                    for tool_call in last_message.tool_calls:
                        if hasattr(tool_call, 'args'):
                            items = extract_actionable_items_from_tool_response(tool_call.args)
                            # Filter for discussion-related items
                            for item in items:
                                if any(keyword in item.get('labels', '').lower() for keyword in ['discussion', 'rfc', 'proposal', 'design', 'review']):
                                    discussion_examples.append(item)
            
            return {
                "github_links": github_links,
                "discussion_examples": discussion_examples
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
                "🔗 Understanding-First Communication Resources"
            )
            
            # Format discussion examples
            discussion_examples_text = ""
            if state.get("discussion_examples"):
                discussion_examples_text = "\n### 💬 Exemplary Discussion Patterns\n\n"
                for example in state["discussion_examples"][:8]:  # Limit to top 8
                    discussion_examples_text += f"- **{example.get('title', 'Unknown')}**\n"
                    discussion_examples_text += f"  - Type: {example.get('type', 'Unknown')}\n"
                    discussion_examples_text += f"  - URL: {example.get('url', 'N/A')}\n"
                    discussion_examples_text += f"  - Labels: {example.get('labels', 'None')}\n"
                    discussion_examples_text += f"  - Summary: {example.get('description', 'No description')}\n\n"
            
            synthesis_prompt = f"""Based on the research conducted, create a comprehensive markdown summary focused on Habit 5 - Seek First to Understand communication patterns in software development.

Structure the summary as follows:

# Habit 5 - Seek First to Understand: Review & Discussion Analysis

**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 👂 Focus: Understanding-First Communication in Development Teams

### Overview
Summarize the key findings related to thoughtful discussion patterns, deep listening, and understanding-first approaches in GitHub repositories.

### Excellent ADR & RFC Processes
[Document repositories with outstanding Architecture Decision Record and RFC processes that show deep listening]

### Thoughtful Code Review Examples
[Showcase specific pull requests and review discussions that demonstrate understanding-first approaches]

### Inclusive Discussion Patterns
[Highlight examples of teams seeking understanding before seeking to be understood]

{discussion_examples_text}

{github_links_markdown}

## 🎯 Learning from Disagreements
[Document specific examples where teams handled disagreements by seeking understanding first]

## 📚 Documentation that Shows Deep Listening
[List repositories with CONTRIBUTING.md, CODE_OF_CONDUCT.md, or other docs that promote understanding]

## 🚀 Action Items for Better Understanding

### This Week
1. [Specific practice to adopt for better listening in reviews]
2. [Template or process to implement for understanding-first discussions]
3. [Documentation to improve for better empathy]

### This Month
1. [Goal for improving team discussion processes]
2. [RFC or ADR process to establish]
3. [Training or practice to implement]

---

Focus on concrete examples and actionable patterns that promote understanding-first communication in technical teams.
"""
            
            synthesis_message = SystemMessage(content=synthesis_prompt)
            ai: AIMessage = llm.invoke(state["messages"] + [synthesis_message], config=config)
            return {
                "messages": [ai],
                "summary": ai.content
            }

        def save_summary_node(state: State, config: RunnableConfig) -> State:
            summary = state.get("summary", "")
            output_path = os.path.join("data", "habits", "habit5_understand.md")
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
        log(f"Error building habit5-understand graph: {e}")
        return None