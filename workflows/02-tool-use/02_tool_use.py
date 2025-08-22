from typing import Dict, Any
import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END


@tool
def get_current_time() -> str:
    """Get the current time."""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@tool 
def calculate(expression: str) -> str:
    """Safely evaluate a mathematical expression."""
    try:
        # Simple calculator - only allow basic operations
        allowed_chars = set('0123456789+-*/.() ')
        if not all(c in allowed_chars for c in expression):
            return "Error: Only basic math operations are allowed"
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"


def build_graph() -> StateGraph:
    """Tool-using chat workflow - can use tools to help with responses."""
    
    def start_node(state: Dict[str, Any]) -> Dict[str, Any]:
        """Entry point of the graph - passes state through unchanged."""
        return state

    def tool_chat_node(state: Dict[str, Any]) -> Dict[str, Any]:
        """Chat node that can use tools to help answer questions."""
        user_message = state.get("user_message", "Hello")
        
        # LLM with tools
        llm = ChatOpenAI(model="gpt-4o-mini")
        tools = [get_current_time, calculate]
        llm_with_tools = llm.bind_tools(tools)
        
        prompt = ChatPromptTemplate.from_template(
            "You are a helpful assistant with access to tools. "
            "Use the tools when appropriate to help answer the user's question.\n"
            "User: {message}"
        )
        
        callbacks = state.get("callbacks", [])
        config = {"callbacks": callbacks} if callbacks else {}
        
        # Get LLM response
        chain = prompt | llm_with_tools
        result = chain.invoke({"message": user_message}, config=config)
        
        # Check if tools were called
        if result.tool_calls:
            tool_results = []
            for tool_call in result.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                
                if tool_name == "get_current_time":
                    tool_result = get_current_time.invoke({})
                elif tool_name == "calculate":
                    tool_result = calculate.invoke(tool_args)
                else:
                    tool_result = "Unknown tool"
                
                tool_results.append(f"Tool {tool_name}: {tool_result}")
            
            # Combine original response with tool results
            response = f"{result.content}\n\nTool Results:\n" + "\n".join(tool_results)
        else:
            response = result.content
        
        return {**state, "response": response}

    # Build the tool-using graph
    graph = StateGraph(dict)
    graph.add_node("start", start_node)
    graph.add_node("tool_chat", tool_chat_node)
    graph.set_entry_point("start")
    graph.add_edge("start", "tool_chat")
    graph.add_edge("tool_chat", END)
    
    return graph
