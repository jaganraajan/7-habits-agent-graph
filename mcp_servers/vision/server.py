#!/usr/bin/env python3
"""
MCP Server for Vision Board Image Generation using Azure OpenAI DALL-E
"""
import os
import sys
import json
import asyncio
from typing import Any, Dict, List

# Add the parent directory to Python path to import tools
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# Now import the tool
from tools.generate_vision_image import generate_vision_image

class VisionMCPServer:
    """Simple MCP server for vision board image generation"""
    
    def __init__(self):
        self.tools = {
            "vision/add_with_image": {
                "name": "vision/add_with_image",
                "description": "Generate a vision board image using Azure OpenAI DALL-E",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "Text description of the vision to generate"
                        },
                        "size": {
                            "type": "string",
                            "enum": ["1024x1024", "1792x1024", "1024x1792"],
                            "default": "1024x1024",
                            "description": "Image size"
                        },
                        "filename_stem": {
                            "type": "string",
                            "description": "Optional base filename"
                        }
                    },
                    "required": ["prompt"]
                }
            }
        }
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Return list of available tools"""
        return list(self.tools.values())
    
    def call_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        """Call a tool with given arguments"""
        if name == "vision/add_with_image":
            return generate_vision_image(
                prompt=arguments["prompt"],
                size=arguments.get("size", "1024x1024"),
                filename_stem=arguments.get("filename_stem")
            )
        else:
            raise ValueError(f"Unknown tool: {name}")

async def main():
    """Simple MCP server implementation"""
    server = VisionMCPServer()
    
    # Read from stdin line by line and respond
    try:
        while True:
            line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            if not line:
                break
            
            try:
                request = json.loads(line.strip())
                
                if request.get("method") == "tools/list":
                    response = {
                        "jsonrpc": "2.0",
                        "id": request.get("id"),
                        "result": {"tools": server.get_tools()}
                    }
                elif request.get("method") == "tools/call":
                    params = request.get("params", {})
                    tool_name = params.get("name")
                    arguments = params.get("arguments", {})
                    
                    result = server.call_tool(tool_name, arguments)
                    response = {
                        "jsonrpc": "2.0",
                        "id": request.get("id"),
                        "result": {"content": [{"type": "text", "text": result}]}
                    }
                else:
                    response = {
                        "jsonrpc": "2.0",
                        "id": request.get("id"),
                        "error": {"code": -32601, "message": "Method not found"}
                    }
                
                print(json.dumps(response), flush=True)
                
            except Exception as e:
                error_response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id") if 'request' in locals() else None,
                    "error": {"code": -32603, "message": str(e)}
                }
                print(json.dumps(error_response), flush=True)
                
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    asyncio.run(main())