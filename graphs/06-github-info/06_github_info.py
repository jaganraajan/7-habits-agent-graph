
from typing import Annotated, TypedDict
from langchain_core.messages import AIMessage, BaseMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from framework.decorators import registered_graph
from framework.mcp_registry import get_mcp_tools
from framework.prompt_manager import get_prompt

# this is the key for the prompt in the prompt manager which gets the Langfuse prompt
PROMPT_KEY = "06_github_info"

# the state that will be passed to each node
class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def init_state() -> State:
    system_prompt = get_prompt(PROMPT_KEY)
    return {"messages": [SystemMessage(content=system_prompt)]}

@registered_graph("06-github-info")
def build_graph() -> StateGraph:
    try:
        # Get GitHub MCP tools
        github_tools = get_mcp_tools("github")
        
        def chat_node(state: State, config: RunnableConfig) -> State:
            llm = ChatOpenAI(model="gpt-4o-mini").bind_tools(github_tools)
            ai: AIMessage = llm.invoke(state["messages"], config=config)
            return {"messages": [ai]}

        def github_info_node(state: State, config: RunnableConfig) -> State:
            # Extract repository information from the conversation
            last_message = state["messages"][-1] if state["messages"] else None
            
            # Default repository information  
            owner = "jaganraajan"
            repo_name = "7-habits-agent-graph"
            
            # Create a helpful summary message
            content = f"""I can help you get GitHub repository information for {owner}/{repo_name}. 

Available GitHub operations:
• List recent commits and pull requests
• Search repositories and code
• Get issue and PR details
• View file contents
• And more GitHub operations

Try asking me: "Show me recent commits and pull requests for this repository" """
            
            ai = AIMessage(content=content)
            return {"messages": [ai]}

        # Create tool node for GitHub tools
        tool_node = ToolNode(github_tools)
        
        # Router function
        def should_call_tool(state: State) -> str:
            last_message = state["messages"][-1]
            return "tools" if getattr(last_message, "tool_calls", None) else "info"

        graph = StateGraph(State)
        graph.add_node("chat", chat_node)
        graph.add_node("tools", tool_node)
        graph.add_node("info", github_info_node)
        
        graph.add_edge(START, "chat")
        graph.add_conditional_edges("chat", should_call_tool, {"tools": "tools", "info": "info"})
        graph.add_edge("tools", "chat")  # Loop back for follow-up
        graph.add_edge("info", END)
        
        return graph
    except Exception as e:
        from framework.log_service import log
        log(f"Error building 06-github-info graph: {e}")
        return None