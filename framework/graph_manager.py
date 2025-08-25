import os
from typing import Dict, Any, Optional
from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import MemorySaver
from langfuse.langchain import CallbackHandler
from langfuse import Langfuse
from dotenv import load_dotenv

from framework.graph_registry import registry

# Cache for compiled graphs
_compiled_graphs: Dict[str, StateGraph] = {}


def get_compiled_graph(name: str) -> Optional[StateGraph]:
    """Build and return a compiled graph by name with persistent checkpointer."""
    
    # Return cached compiled graph if it exists
    if name in _compiled_graphs:
        return _compiled_graphs[name]
    
    # Get the build function from registry
    build_function = registry.get_build_function(name)
    if not build_function:
        return None
    
    try:
        # Build the graph
        graph = build_function()
        # Create a persistent checkpointer for this graph
        checkpointer = MemorySaver()
        # Compile the graph with the checkpointer
        compiled_graph = graph.compile(checkpointer=checkpointer)
        # Cache the compiled graph
        _compiled_graphs[name] = compiled_graph
        
        return compiled_graph
        
    except Exception as e:
        print(f"Error building graph '{name}': {e}")
        return None


async def invoke_graph(
    graph_name: str,
    message: str,
    thread_id: Optional[str] = None,
    is_new_thread: bool = False,
) -> str:
    """Invoke a graph with message handling and state management."""
    from langchain_core.messages import HumanMessage
    
    # Get the compiled graph
    graph = get_compiled_graph(graph_name)
    if not graph:
        raise ValueError(f"Could not load graph '{graph_name}'")
    
    # Get the graph module for init_state
    graph_module = registry.get_graph_module(graph_name)
    if not graph_module:
        raise ValueError(f"Could not load graph module '{graph_name}'")
    
    # Prepare input based on whether this is a new thread
    if is_new_thread:
        # First message: initialize with system prompt + user message
        initial_state = graph_module.init_state()
        input_data = {
            "messages": initial_state["messages"] + [HumanMessage(content=message)]
        }
    else:
        # Subsequent messages: send only the user message delta
        input_data = {
            "messages": [HumanMessage(content=message)]
        }
    
    # Setup Langfuse tracking
    langfuse_handler = CallbackHandler()
    config = {
        "callbacks": [langfuse_handler],
        "configurable": {"thread_id": thread_id}
    }
    
    # Invoke the graph
    result = await graph.ainvoke(input_data, config)
    
    # Extract and return the response message
    response_messages = result.get("messages", [])
    if response_messages:
        return response_messages[-1].content
    else:
        return "No response generated"