"""Simplified graph registry using only @registered_graph decorators."""

import importlib
import importlib.util
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from framework.decorators.registered_graph import get_registered_graphs

from framework.log_service import log


@dataclass
class GraphInfo:
    """Information about a discovered graph."""
    name: str
    build_function: callable
    module_path: str
    module: Any = None


class GraphRegistry:
    """Clean registry that imports modules to trigger @registered_graph decorators."""
    
    def __init__(self):
        self._graphs: Dict[str, GraphInfo] = {}
        self._discovered: bool = False
        self._modules: Dict[str, Any] = {}  # Store imported modules
    
    def _discover_graphs(self) -> None:
        """Import modules to trigger @registered_graph decorators."""
        project_root = Path(__file__).parent.parent
        graphs_dir = project_root / "graphs"
        
        if not graphs_dir.exists():
            log(f"Warning: Graphs directory not found at {graphs_dir}")
            return
        
        # Import Python files in root graphs directory
        for py_file in graphs_dir.glob("*.py"):
            if py_file.name.startswith('__'):
                continue    
                
            module_name = py_file.stem
            try:
                spec = importlib.util.spec_from_file_location(
                    f"graphs.{module_name}", 
                    py_file
                )
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    # Store the module for later access
                    self._store_module(f"graphs.{module_name}", module)
            except Exception as e:
                log(f"Warning: Could not import {module_name}: {e}")
        
        # Import Python files in subdirectories
        for subdir in graphs_dir.iterdir():
            if subdir.is_dir():
                for py_file in subdir.glob("*.py"):
                    if py_file.name.startswith('__'):
                        continue
                    
                    module_name = py_file.stem
                    try:
                        spec = importlib.util.spec_from_file_location(
                            f"graphs.{subdir.name}.{module_name}", 
                            py_file
                        )
                        if spec and spec.loader:
                            module = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(module)
                            # Store the module for later access
                            self._store_module(f"graphs.{subdir.name}.{module_name}", module)
                    except Exception as e:
                        log(f"Warning: Could not import {subdir.name}.{module_name}: {e}")
        
        # Now get all the registered graphs from the decorator system
        registered_graphs = get_registered_graphs()
        
        for name, build_func in registered_graphs.items():
            module_path = getattr(build_func, '__module__', 'unknown')
            # Find the corresponding module we imported
            module = self._modules.get(module_path)
            self._graphs[name] = GraphInfo(
                name=name,
                build_function=build_func,
                module_path=module_path,
                module=module
            )
    
    def _store_module(self, module_path: str, module: Any) -> None:
        """Store an imported module for later access."""
        self._modules[module_path] = module
    
    def _ensure_discovered(self) -> None:
        """Ensure graphs have been discovered."""
        if not self._discovered:
            self._discover_graphs()
            self._discovered = True
    
    def list_graphs(self) -> List[GraphInfo]:
        """Get a list of all discovered graphs."""
        self._ensure_discovered()
        return list(self._graphs.values())
    
    def get_graph_info(self, name: str) -> Optional[GraphInfo]:
        """Get graph info by name."""
        self._ensure_discovered()
        return self._graphs.get(name)
    
    def get_build_function(self, name: str) -> Optional[callable]:
        """Get the build function for a graph by name."""
        self._ensure_discovered()
        graph_info = self._graphs.get(name)
        return graph_info.build_function if graph_info else None
    
    def get_graph_module(self, name: str) -> Optional[Any]:
        """Get the graph module by name to access init_state and other functions."""
        self._ensure_discovered()
        graph_info = self._graphs.get(name)
        if not graph_info:
            return None
        
        # Return the stored module directly
        return graph_info.module


# Global singleton registry instance
registry = GraphRegistry()

# Export the singleton registry
__all__ = ["registry"]