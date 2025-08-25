from operator import add
from typing import Any, Annotated, Dict, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from framework.log_service import log
from framework.prompt_manager import get_prompt
from framework.decorators import registered_graph
from tools.get_current_datetime import get_current_datetime
from tools.mcp.mcp_registry import get_mcp_tools, init_mcp_registry
from tools.search_web import search_web

PROMPT_KEY = "02_tooluse"

# the state that will be passed to each node
class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def init_state() -> State:
    system_prompt = get_prompt(PROMPT_KEY)
    return {"messages": [SystemMessage(content=system_prompt)]}

@registered_graph("02-tooluse")
def build_graph() -> StateGraph:
    # Get MCP filesystem tools (registry initialized in main.py)
    filesystem_tools = get_mcp_tools("filesystem")
    
    # Combine all tools
    all_tools = [
        *filesystem_tools, 
        get_current_datetime,
        search_web
    ]
    
    def chat_node(state: State, config: RunnableConfig) -> State:

        llm = ChatOpenAI(model="gpt-4o-mini").bind_tools(all_tools)
        ai: AIMessage = llm.invoke(state["messages"], config=config)
        
        return {"messages": [ai]}

    # Create special ToolNode to execute tool calls
    tool_node = ToolNode(all_tools)
    
    # Router function to decide between tools and end
    def should_call_tool(state: State) -> str:
        last_message = state["messages"][-1]
        return "tools" if getattr(last_message, "tool_calls", None) else "end"

    # initialize graph
    graph = StateGraph(State)

    # add nodes
    graph.add_node("chat", chat_node)
    graph.add_node("tools", tool_node)
    
    # add edges
    graph.add_edge(START, "chat")
    graph.add_conditional_edges("chat", should_call_tool, {"tools": "tools", "end": END})
    graph.add_edge("tools", END)   

    # Alternatively 
    # graph.add_edge("tools", "chat")
    # This would allow the LLM to call tools multiple time in a loop creating the ReAct pattern
    # LangGraph has a prebuilt graph for this called
    # agent = create_react_agent(model, tools, checkpointer=memory)
    
    return graph
