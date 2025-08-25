"""Graph registration decorator for auto-discovery of LangGraph workflows."""

from typing import Dict, Callable
from langgraph.graph import StateGraph

# Global registry to store registered graph functions
_graph_registry: Dict[str, Callable[[], StateGraph]] = {}

def registered_graph(name: str):
    def decorator(func: Callable[[], StateGraph]) -> Callable[[], StateGraph]:
        _graph_registry[name] = func
        return func
    return decorator

def get_registered_graphs() -> Dict[str, Callable[[], StateGraph]]:
    """Get all registered graph functions."""
    return _graph_registry.copy()


def get_registered_graph(name: str) -> Callable[[], StateGraph] | None:
    """Get a specific registered graph function by name."""
    return _graph_registry.get(name)
