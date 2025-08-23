from typing import Dict, Any, TypedDict, Annotated
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END, START      
from framework.prompt_manager import prompt_manager
from langchain_core.messages import BaseMessage
from operator import add
from langchain_community.tools import DuckDuckGoSearchRun
from langgraph.prebuilt import ToolNode

PROMPT_KEY = "persona"

# the state that will be passed to each node
class State(TypedDict):
    user_message: str
    messages: Annotated[list[BaseMessage], add]

def build_graph() -> StateGraph:
    
    # Initialize DuckDuckGo search tool
    search_tool = DuckDuckGoSearchRun()
    
    def chat_node(state: State) -> State:
        # get system prompt
        system_prompt = prompt_manager.get_production_prompt(PROMPT_KEY)
        
        # get existing messages or start with system prompt
        existing_messages = state.get("messages", [])
        
        # ensure system prompt is always first (add it if messages is empty)
        if not existing_messages:
            existing_messages = [SystemMessage(content=system_prompt)]
        
        # add the new user message if provided
        if state.get("user_message"):
            messages = [*existing_messages, HumanMessage(content=state.get("user_message"))]
        else:
            messages = existing_messages

        # initialize llm with tools bound
        llm = ChatOpenAI(model="gpt-4o-mini").bind_tools([search_tool])

        # invoke llm
        result = llm.invoke(messages)
        
        # return response with updated messages including the LLM response
        return {"messages": [result]}

    # Create ToolNode to execute tool calls
    tool_node = ToolNode([search_tool])
    
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
    graph.add_edge("tools", "chat")  # after tool runs, go back to LLM
    
    return graph
