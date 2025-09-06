# framework/mcp_registry.py
import json
import os
from typing import Dict, List, Optional

from langchain_mcp_adapters.client import MultiServerMCPClient

from framework.log_service import log

# replaces placeholders like ${VAR} or ${VAR:-default} in config file with real environment variable values.
def _expand(value: str) -> str:
    """Expand ${VAR} (required) and ${VAR:-default} (optional)."""
    import re
    def repl(m):
        inner = m.group(1)
        if ":-" in inner:
            var, default = inner.split(":-", 1)
            result = os.getenv(var, default)
        else:
            val = os.getenv(inner)
            if val is None:
                raise KeyError(f"Missing env var: {inner}")
            result = val
        
        # Convert relative paths to absolute paths for Docker bind mounts
        if result.startswith('./') or result.startswith('../') or (not result.startswith('/') and '/' in result):
            result = os.path.abspath(result)
        
        return result
    return re.sub(r"\$\{([^}]+)\}", repl, value)


class _MCPRegistry:
    _client: Optional[MultiServerMCPClient] = None
    _tools_by_server: Dict[str, List] = {}

    async def initialize(self, config_path: str = "mcp_config.json") -> None:
        with open(config_path) as f:
            cfg = json.load(f)

        connections: Dict[str, dict] = {}
        for name, s in cfg.get("mcpServers", {}).items():
            # Support both 'transport' and 'type' for HTTP-based servers
            transport = s.get("transport") or ("stdio" if "command" in s else None) or ("streamable_http" if s.get("type") == "http" else None)
            if transport == "stdio":
                args = [_expand(x) for x in s.get("args", [])]
                env = {k: _expand(v) for k, v in s.get("env", {}).items()}
                connections[name] = {
                    "transport": "stdio",
                    "command": s["command"],
                    "args": args,
                    "env": env,
                }
            elif transport in ("sse", "streamable_http"):
                connections[name] = {
                    "transport": transport,
                    "url": s["url"],
                    **({"headers": s["headers"]} if "headers" in s else {}),
                }
            else:
                raise ValueError(f"Unsupported transport: {transport}")

        self._client = MultiServerMCPClient(connections)
        self._tools_by_server.clear()

        for name in connections.keys():
            tools = await self._client.get_tools(server_name=name)
            self._tools_by_server[name] = tools
            log(f"[MCP] Connected to '{name}' with {len(tools)} tools")

    def get_tools(self, server_name: str) -> List:
        return self._tools_by_server.get(server_name, [])
    
    def get_all_servers_tools(self) -> Dict[str, List]:
        """Get all tools organized by server name."""
        return dict(self._tools_by_server)


_registry = _MCPRegistry()


async def init_mcp_registry(config_path: str = "mcp_config.json") -> None:
    log(f"[MCP] Initializing MCP registry from {config_path}...")
    await _registry.initialize(config_path)
    log(f"[MCP] MCP registry initialized.")


def get_mcp_tools(server_name: str) -> List:
    return _registry.get_tools(server_name)


def get_all_mcp_servers_tools() -> Dict[str, List]:
    """Get all MCP tools organized by server name."""
    return _registry.get_all_servers_tools()
