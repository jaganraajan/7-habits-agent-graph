import os
from typing import Dict, Any, Optional
from langgraph.graph import StateGraph
from langfuse.langchain import CallbackHandler
from langfuse import Langfuse
from dotenv import load_dotenv

def invoke_graph(
    graph: StateGraph, 
    input_state: Dict[str, Any], 
) -> Dict[str, Any]:

    langfuse_handler = CallbackHandler()

    default_config = {
        "callbacks": [langfuse_handler]
    }

    return graph.invoke(input_state, default_config)


def build_graph(name: str) -> Optional[StateGraph]:
    """Build and return a compiled graph by name."""
    from workflows.workflow_registry import registry
    
    graph_info = registry.get_graph(name)
    if graph_info:
        return graph_info.build_function().compile()
    return None