#!/usr/bin/env python3
"""
CLI script to run the Habit 1 - Be Proactive workflow
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from framework.graph_manager import invoke_graph
from framework.mcp_registry import init_mcp_registry
from dotenv import load_dotenv

async def run_habit1_proactive():
    """Run the Habit 1 - Be Proactive workflow."""
    print("🚀 Starting Habit 1 - Be Proactive Workflow")
    print("=" * 50)
    
    try:
        # Initialize MCP registry
        print("🔧 Initializing MCP connections...")
        await init_mcp_registry()
        
        # Run the workflow
        print("📊 Executing GitHub research workflow...")
        result = await invoke_graph(
            graph_name="habit1-proactive",
            initial_message="Research GitHub repositories for agentic/MCP content and generate a proactive summary.",
            config={}
        )
        
        if result:
            print("✅ Workflow completed successfully!")
            print("📄 Summary saved to: data/habits/habit1_proactive_summary.md")
            print("🌐 View in web interface: http://localhost:5000")
        else:
            print("❌ Workflow failed to complete.")
            
    except Exception as e:
        print(f"❌ Error running workflow: {e}")
        print("💡 Make sure you have:")
        print("   - Set GITHUB_TOKEN in your .env file")
        print("   - Set AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT")
        print("   - All MCP servers are properly configured")

def main():
    """Main entry point."""
    load_dotenv()
    
    print("🎯 7 Habits Agent Graph - Habit 1: Be Proactive")
    print()
    
    # Check for required environment variables
    required_vars = ['AZURE_OPENAI_API_KEY', 'AZURE_OPENAI_ENDPOINT']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n💡 Please set these in your .env file")
        return
    
    # Run the workflow
    asyncio.run(run_habit1_proactive())

if __name__ == "__main__":
    main()