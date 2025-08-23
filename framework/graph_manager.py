import os
from typing import Dict, Any, Optional
from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import MemorySaver
from langfuse.langchain import CallbackHandler
from langfuse import Langfuse
from dotenv import load_dotenv

def invoke_graph(
    graph: StateGraph, 
    input_state: Dict[str, Any],
    thread_id: Optional[str] = None,
) -> Dict[str, Any]:

    langfuse_handler = CallbackHandler()

    config = {
        "callbacks": [langfuse_handler],
        "configurable": {"thread_id": thread_id}
    }
    
    return graph.invoke(input_state, config)


def build_graph(name: str) -> Optional[StateGraph]:
    """Build and return a compiled graph by name."""
    from workflows.graph_registry import registry
    
    # Return the pre-compiled graph with persistent checkpointer
    return registry.get_compiled_graph(name)