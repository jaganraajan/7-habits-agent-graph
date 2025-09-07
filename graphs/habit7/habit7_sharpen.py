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
# from framework.prompt_manager import get_prompt
from framework.log_service import log
from framework.github_utils import (
    extract_github_links_from_messages,
    format_github_links_for_markdown,
    extract_actionable_items_from_tool_response
)

# this is the key for the prompt in the prompt manager which gets the Langfuse prompt
PROMPT_KEY = "habit7_sharpen"

# the state that will be passed to each node
class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    github_links: list[str]
    learning_opportunities: list[dict]
    summary: str

def init_state() -> State:
    system_prompt = PROMPT_KEY or """You are a GitHub research assistant focused on continuous learning and growth opportunities in Large Language Models (LLMs), agentic AI, and advanced AI development.

Your mission is to find excellent examples of repositories, resources, and opportunities that support skill development, learning, and professional growth in the fields of LLMs, agentic AI, autonomous agents, and related AI technologies.

Focus areas:
1. Repositories with high-quality LLM/agentic AI tutorials, guides, and educational content
2. Projects with "good first issue" and mentorship opportunities in LLMs/agentic AI
3. New releases and changelogs in LLM/agentic AI projects that offer learning insights
4. Documentation and resources for building, fine-tuning, or deploying LLMs and agentic systems
5. Communities and organizations that actively foster learning and growth in LLMs and agentic AI

Look for patterns where projects:
- Provide structured learning paths and tutorials for LLMs/agentic AI
- Offer beginner-friendly contribution opportunities in AI/LLM projects
- Have active mentorship and community support for AI/LLM contributors
- Regularly release updates with learning opportunities in LLM/agentic AI
- Document their processes for educational purposes in the AI/LLM space
- Foster knowledge sharing and skill development in LLMs, agentic AI, and autonomous systems"""
    return {
        "messages": [SystemMessage(content=system_prompt)],
        "github_links": [],
        "learning_opportunities": [],
        "summary": ""
    }

@registered_graph("habit7-sharpen")
def build_graph() -> StateGraph:
    load_dotenv()
    try:
        github_tools = get_mcp_tools("github")

        def data_collection_node(state: State, config: RunnableConfig) -> State:
            """Collect data focused on learning and growth opportunities"""
            subscription_key = os.getenv("AZURE_OPENAI_API_KEY")
            api_version = "2024-12-01-preview"
            llm = AzureChatOpenAI(
                api_key=subscription_key,
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_version=api_version,
                deployment_name="gpt-4o-mini"
            ).bind_tools(github_tools)
            
            research_prompt = """
Search for repositories and opportunities that promote continuous learning and skill development in Large Language Models (LLMs), agentic AI, and autonomous agent systems.

SEARCH TARGETS:
1. Look for repositories with "good first issue" labels and mentorship programs in LLM/agentic AI projects
2. Search for LLM/agentic AI learning resources, tutorials, and educational content
3. Find repositories with excellent documentation and learning paths for LLMs, agentic AI, and autonomous agents
4. Look for recent releases in LLM/agentic AI projects with learning opportunities
5. Search for communities that actively support skill development in LLMs and agentic AI

Use these specific search queries:
- search_issues: query="label:'good first issue' OR label:beginner OR label:mentor topic:llm OR topic:agent OR topic:autonomous-agents"
- search_repositories: query="llm OR agentic OR autonomous OR langchain OR openai OR gpt OR llama OR transformers OR ai OR tutorial OR learning OR education topic:llm"
- search_repositories: query="awesome-llm OR awesome-agents OR awesome-autonomous-agents OR resources OR guide"
- list_releases: Look for recent releases in LLM/agentic AI projects with detailed changelogs
- get_file_contents: Look for LEARNING.md, TUTORIAL.md, AGENT.md, LLM.md, docs/ directories, CHANGELOG.md
- search_repositories: query="topic:llm OR topic:agentic-ai OR topic:autonomous-agents OR topic:beginner-friendly OR topic:mentorship"

Focus on finding concrete learning opportunities and growth resources in LLMs, agentic AI, and autonomous agent development.
"""
            research_message = SystemMessage(content=research_prompt)
            ai: AIMessage = llm.invoke(state["messages"] + [research_message], config=config)
            return {"messages": [ai]}

        def link_extraction_node(state: State, config: RunnableConfig) -> State:
            """Extract GitHub links and learning opportunities from tool responses"""
            github_links = extract_github_links_from_messages(state["messages"])
            
            # Extract learning opportunities
            learning_opportunities = []
            if state["messages"]:
                last_message = state["messages"][-1]
                if isinstance(last_message, AIMessage) and hasattr(last_message, 'tool_calls'):
                    for tool_call in last_message.tool_calls:
                        if hasattr(tool_call, 'args'):
                            items = extract_actionable_items_from_tool_response(tool_call.args)
                            # Filter for LLM/agentic AI learning-related items
                            for item in items:
                                item_text = f"{item.get('title', '')} {item.get('description', '')} {item.get('labels', '')}".lower()
                                if any(keyword in item_text for keyword in [
                                    'llm', 'agentic', 'autonomous', 'langchain', 'openai', 'gpt', 'llama', 'transformers',
                                    'ai', 'learning', 'tutorial', 'beginner', 'good first issue', 'mentor', 'education', 'guide', 'agent']):
                                    learning_opportunities.append(item)
            return {
                "github_links": github_links,
                "learning_opportunities": learning_opportunities
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
                "🔗 Learning & Growth Resources"
            )
            
            # Format learning opportunities
            learning_opportunities_text = ""
            if state.get("learning_opportunities"):
                learning_opportunities_text = "\n### 🌱 Immediate Learning Opportunities\n\n"
                for opportunity in state["learning_opportunities"][:10]:  # Limit to top 10
                    learning_opportunities_text += f"- **{opportunity.get('title', 'Unknown')}**\n"
                    learning_opportunities_text += f"  - Type: {opportunity.get('type', 'Unknown')}\n"
                    learning_opportunities_text += f"  - URL: {opportunity.get('url', 'N/A')}\n"
                    learning_opportunities_text += f"  - Labels: {opportunity.get('labels', 'None')}\n"
                    learning_opportunities_text += f"  - Summary: {opportunity.get('description', 'No description')}\n\n"
            
            synthesis_prompt = f"""Based on the research conducted, create a comprehensive markdown summary focused on Habit 7 - Sharpen the Saw, with a special emphasis on learning and growth opportunities in Large Language Models (LLMs), agentic AI, and autonomous agent development.

Structure the summary as follows:

# Habit 7 - Sharpen the Saw: LLMs & Agentic AI Learning & Growth Opportunities

**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 🔧 Focus: Continuous Learning and Skill Development in LLMs & Agentic AI

### Overview
Summarize the key findings related to LLMs, agentic AI, and autonomous agent learning resources, growth opportunities, and skill development available in GitHub repositories.

### Excellence in LLM/Agentic AI Learning Resources
[List repositories with outstanding LLM/agentic AI tutorials, guides, and educational content]

### Beginner-Friendly Contribution Opportunities in LLM/Agentic AI
[Document repositories with great "good first issue" programs and mentorship in LLM/agentic AI]

### Recent Releases with LLM/Agentic AI Learning Value
[Highlight new releases, features, and updates in LLM/agentic AI projects that offer learning opportunities]

{learning_opportunities_text}

{github_links_markdown}

## 📚 Structured LLM/Agentic AI Learning Paths
[Document repositories that provide clear, progressive learning experiences in LLMs and agentic AI]

### Active LLM/Agentic AI Learning Communities
[Highlight communities and projects that actively foster skill development in LLMs and agentic AI]

### Mentorship and Growth Programs in LLM/Agentic AI
[List projects with active mentorship, code review, and growth support in LLMs and agentic AI]

### Knowledge Sharing Excellence in LLM/Agentic AI
[Document projects that excel at sharing knowledge and teaching in LLMs and agentic AI]

## 🎯 Personal Development Action Plan (LLMs & Agentic AI)

### This Week - Skill Building
1. [Specific LLM/agentic AI tutorial or resource to explore]
2. [Beginner issue to tackle for LLM/agentic AI learning]
3. [Documentation to read for LLM/agentic AI growth]

### This Month - Knowledge Expansion  
1. [LLM/agentic AI learning project to pursue]
2. [Community to join for LLM/agentic AI growth]
3. [Skill area to develop in LLMs/agentic AI]

### This Quarter - Mastery Development
1. [Advanced LLM/agentic AI learning goal to achieve]
2. [Mentorship opportunity to pursue in LLMs/agentic AI]
3. [Knowledge sharing contribution to make in LLMs/agentic AI]

---

Focus on concrete learning opportunities that promote continuous skill development and professional growth in LLMs, agentic AI, and autonomous agent systems.
"""
            synthesis_message = SystemMessage(content=synthesis_prompt)
            ai: AIMessage = llm.invoke(state["messages"] + [synthesis_message], config=config)
            return {
                "messages": [ai],
                "summary": ai.content
            }

        def save_summary_node(state: State, config: RunnableConfig) -> State:
            summary = state.get("summary", "")
            output_path = os.path.join("data", "habits", "habit7_sharpen.md")
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
        log(f"Error building habit7-sharpen graph: {e}")
        return None