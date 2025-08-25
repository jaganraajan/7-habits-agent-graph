"""
Simple MCP Registry Singleton

Manages individual MCP server connections and provides access to their tools.
Initializes all servers at startup for the lifetime of the process.
"""

import asyncio
import json
import os
from pathlib import Path
from typing import Dict, List, Optional

from langchain_mcp_adapters.client import MultiServerMCPClient


class MCPRegistry:
    """Singleton registry for MCP server connections and tools."""
    
    _instance: Optional['MCPRegistry'] = None
    _initialized: bool = False
    
    def __new__(cls) -> 'MCPRegistry':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.client: Optional[MultiServerMCPClient] = None
            self.server_tools: Dict[str, List] = {}
            self._initialized = True
    
    async def initialize(self, config_path: str = "mcp_config.json"):
        """Initialize all MCP servers from config."""
        config = self._load_config(config_path)
        
        # Convert config to MultiServerMCPClient format
        client_config = {}
        for server_name, server_config in config.get("mcpServers", {}).items():
            client_config[server_name] = {
                "command": server_config["command"],
                "args": server_config["args"],
                "transport": "stdio"
            }
            
            # Add environment variables if specified
            if "env" in server_config:
                client_config[server_name]["env"] = {}
                for env_var, template in server_config["env"].items():
                    if template.startswith("${") and template.endswith("}"):
                        env_name = template[2:-1]  # Remove ${ and }
                        env_value = os.getenv(env_name, "")
                        client_config[server_name]["env"][env_var] = env_value
                    else:
                        client_config[server_name]["env"][env_var] = template
        
        # Initialize the client
        self.client = MultiServerMCPClient(client_config)
        
        # Get all tools and organize by server
        all_tools = await self.client.get_tools()
        
        # For now, put all tools under each server name
        # In a real implementation, you'd need to track which tools come from which server
        for server_name in client_config.keys():
            self.server_tools[server_name] = all_tools
            print(f"Connected to MCP server '{server_name}' with {len(all_tools)} tools")
    
    def _load_config(self, config_path: str) -> dict:
        """Load MCP configuration and replace environment variables."""
        with open(config_path) as f:
            config = json.load(f)
        
        # Replace environment variables in args (only for special cases like path resolution)
        for server_config in config.get("mcpServers", {}).values():
            for i, arg in enumerate(server_config.get("args", [])):
                # Handle special case for MCP_WORKING_DIR (convert to absolute path)
                if "${MCP_WORKING_DIR}" in arg:
                    working_dir = os.getenv("MCP_WORKING_DIR", ".")
                    abs_path = str(Path(working_dir).resolve())
                    server_config["args"][i] = arg.replace("${MCP_WORKING_DIR}", abs_path)
        
        return config
    
    def get_tools(self, server_name: str) -> List:
        """Get tools from a specific server."""
        return self.server_tools.get(server_name, [])
    
    def get_all_tools(self) -> List:
        """Get all tools from all servers."""
        if self.client is None:
            return []
        # Return tools from the first server (since they're all the same in this simple version)
        all_tools = []
        for tools in self.server_tools.values():
            all_tools.extend(tools)
            break  # Just get tools once since they're duplicated
        return all_tools
    
    def list_servers(self) -> List[str]:
        """List all connected server names."""
        return list(self.server_tools.keys())


# Global registry instance
mcp_registry = MCPRegistry()


# Convenience functions
async def init_mcp_registry(config_path: str = "mcp_config.json"):
    """Initialize the global MCP registry."""
    await mcp_registry.initialize(config_path)


def get_mcp_tools(server_name: str) -> List:
    """Get tools from a specific MCP server."""
    return mcp_registry.get_tools(server_name)


def get_all_mcp_tools() -> List:
    """Get all tools from all MCP servers."""
    return mcp_registry.get_all_tools()


def list_mcp_servers() -> List[str]:
    """List all available MCP servers."""
    return mcp_registry.list_servers()