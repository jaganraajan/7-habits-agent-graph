"""Graph registry system for managing different LangGraph workflows."""

import os
import sys
import importlib.util
from typing import Dict, Any, Callable, List, Optional
from dataclasses import dataclass
from pathlib import Path
from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import MemorySaver


@dataclass
class GraphInfo:
    """Information about a registered graph."""
    name: str
    build_function: Callable[[], StateGraph]
    module_path: str
    compiled_graph: Optional[StateGraph] = None
    checkpointer: Optional[MemorySaver] = None


class GraphRegistry:
    """Registry for managing and discovering LangGraph workflows."""
    
    def __init__(self):
        self._graphs: Dict[str, GraphInfo] = {}
        self._discover_graphs()
    
    def _discover_graphs(self) -> None:
        """Automatically discover graphs in the workflows directory."""
        workflows_dir = Path(__file__).parent
        
        if not workflows_dir.exists():
            return
        
        for workflow_dir in workflows_dir.iterdir():
            if not workflow_dir.is_dir() or workflow_dir.name.startswith('__'):
                continue
                
            self._load_workflow(workflow_dir)
    
    def _load_workflow(self, workflow_dir: Path) -> None:
        """Load a workflow from a directory."""
        # Look for Python files in the workflow directory
        python_files = list(workflow_dir.glob("*.py"))
        
        for py_file in python_files:
            if py_file.name.startswith('__'):
                continue
                
            try:
                # Load the module with a unique name to avoid conflicts
                module_name = f"{workflow_dir.name}_{py_file.stem}"
                spec = importlib.util.spec_from_file_location(module_name, py_file)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    
                    # Add the workflow directory to sys.path temporarily
                    import sys
                    original_path = sys.path.copy()
                    if str(workflow_dir) not in sys.path:
                        sys.path.insert(0, str(workflow_dir))
                    
                    try:
                        spec.loader.exec_module(module)
                        
                        # Check if it has a build_graph function
                        if hasattr(module, 'build_graph'):
                            workflow_name = workflow_dir.name
                            
                            # Create a persistent checkpointer for this graph
                            checkpointer = MemorySaver()
                            
                            # Compile the graph immediately with the checkpointer
                            compiled_graph = module.build_graph().compile(checkpointer=checkpointer)
                            
                            graph_info = GraphInfo(
                                name=workflow_name,
                                build_function=module.build_graph,
                                module_path=str(py_file),
                                compiled_graph=compiled_graph,
                                checkpointer=checkpointer
                            )
                            
                            self._graphs[workflow_name] = graph_info
                    finally:
                        # Restore original sys.path
                        sys.path = original_path
                        
            except Exception as e:
                print(f"Warning: Could not load workflow from {py_file}: {e}")
                import traceback
                traceback.print_exc()
    

    def list_graphs(self) -> List[GraphInfo]:
        """Get a list of all registered graphs."""
        return list(self._graphs.values())
    
    def get_graph(self, name: str) -> Optional[GraphInfo]:
        """Get a specific graph by name."""
        return self._graphs.get(name)
    
    def get_compiled_graph(self, name: str) -> Optional[StateGraph]:
        """Get a compiled graph by name."""
        graph_info = self._graphs.get(name)
        return graph_info.compiled_graph if graph_info else None
    
    def get_checkpointer(self, name: str) -> Optional[MemorySaver]:
        """Get the checkpointer for a specific graph."""
        graph_info = self._graphs.get(name)
        return graph_info.checkpointer if graph_info else None
    



# Global singleton registry instance
registry = GraphRegistry()

# Export the singleton registry
__all__ = ["registry"]
