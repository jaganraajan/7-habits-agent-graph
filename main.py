import os
import sys
import asyncio
from dotenv import load_dotenv
from framework.chat_ui import run_chat_ui
from tools.mcp.mcp_registry import init_mcp_registry

async def init_app() -> None:
    print("Initializing MCP registry...")
    await init_mcp_registry()
    print(f"MCP registry initialized.")

def main() -> None:
    load_dotenv()
    asyncio.run(init_app())
    run_chat_ui()

if __name__ == "__main__":      
    main()