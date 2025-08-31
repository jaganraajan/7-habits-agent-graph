#!/usr/bin/env python3
"""
TODO App Usage Examples

This script demonstrates how the TODO app would work when connected to a real MCP server.
Since we don't have the actual MCP server running, this shows the expected behavior.
"""

import sys
import os
from pathlib import Path

# Add the project root to the path so we can import prompts
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from prompts import prompts

def show_exported_prompts():
    """Display the exported prompts for the TODO app"""
    print("🔧 Exported TODO App Prompts:")
    print("=" * 50)
    
    for prompt in prompts:
        print(f"\n📋 {prompt['label']} ({prompt['id']})")
        print(f"   Description: {prompt['description']}")
        print(f"   Example Input: {prompt['inputExample']}")
    
    print("\n" + "=" * 50)

def show_sample_interactions():
    """Show sample user interactions with the TODO app"""
    print("\n💬 Sample User Interactions:")
    print("=" * 50)
    
    examples = [
        {
            "user": "Add a new TODO: Buy groceries",
            "expected": "Uses add_todo_prompt with title: 'Buy groceries'",
            "ai_response": "I've added 'Buy groceries' to your TODO list!"
        },
        {
            "user": "Show me all my TODO items", 
            "expected": "Uses list_todos_prompt",
            "ai_response": "Here are your TODO items:\n1. Buy groceries (pending)\n2. Call dentist (pending)"
        },
        {
            "user": "Mark TODO item 1 as completed",
            "expected": "Uses complete_todo_prompt with id: 1", 
            "ai_response": "I've marked 'Buy groceries' as completed!"
        },
        {
            "user": "Delete TODO item 2",
            "expected": "Uses delete_todo_prompt with id: 2",
            "ai_response": "I've deleted 'Call dentist' from your TODO list."
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n{i}. User: \"{example['user']}\"")
        print(f"   System: {example['expected']}")
        print(f"   AI: {example['ai_response']}")
    
    print("\n" + "=" * 50)

def show_graph_info():
    """Show information about the TODO graph"""
    print("\n🔍 TODO Graph Information:")
    print("=" * 50)
    
    print("Graph ID: 08-todo-app")
    print("Location: graphs/08-todo-app/08_todo_app.py")
    print("MCP Server: http://localhost:3000/mcp (SSE transport)")
    print("Operations: Add, List, Complete, Delete TODOs")
    print("Integration: Follows same pattern as GitHub and Vision board graphs")
    
    print("\n📁 Required Files:")
    print("✅ graphs/08-todo-app/08_todo_app.py - Main graph implementation")
    print("✅ prompts.py - Exported prompt definitions")
    print("✅ mcp_config.json - MCP server configuration")
    print("✅ README.md - Updated with TODO app documentation")
    
    print("\n" + "=" * 50)

def main():
    """Main demonstration function"""
    print("🎯 TODO App MCP Integration Demo")
    print("This demonstrates the completed TODO app integration.\n")
    
    show_exported_prompts()
    show_sample_interactions()
    show_graph_info()
    
    print("\n🚀 To use the TODO app:")
    print("1. Start your TODO MCP server at http://localhost:3000/mcp")
    print("2. Ensure MCP_WORKING_DIR and other env vars are set")
    print("3. Run: python main.py")
    print("4. Select '08-todo-app' from the workflow dropdown")
    print("5. Try the sample queries shown above")
    
    print("\n✨ The integration is complete and ready to use!")

if __name__ == "__main__":
    main()