import os
from dotenv import load_dotenv
from typing import Annotated, TypedDict
from langchain_core.messages import AIMessage, BaseMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import AzureChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from framework.decorators import registered_graph
from framework.mcp_registry import get_mcp_tools
from framework.prompt_manager import get_prompt

# this is the key for the prompt in the prompt manager which gets the Langfuse prompt
PROMPT_KEY = "08_todo_app"

# the state that will be passed to each node
class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def init_state() -> State:
    system_prompt = get_prompt(PROMPT_KEY)
    return {"messages": [SystemMessage(content=system_prompt)]}

@registered_graph("08-todo-app")
def build_graph() -> StateGraph:
    load_dotenv()
    try:
        # Get TODO MCP tools
        todo_tools = get_mcp_tools("todo")
        
        def chat_node(state: State, config: RunnableConfig) -> State:
            subscription_key = os.getenv("AZURE_OPENAI_API_KEY")
            api_version = "2024-12-01-preview"

            # Initialize LLM
            llm = AzureChatOpenAI(
                api_key=subscription_key,
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_version=api_version,
                deployment_name="gpt-4o-mini"
            ).bind_tools(todo_tools)
            ai: AIMessage = llm.invoke(state["messages"], config=config)
            return {"messages": [ai]}

        def todo_info_node(state: State, config: RunnableConfig) -> State:
            # Create a helpful introduction message about TODO capabilities
            content = """I can help you manage your TODO items! 

Here's what I can do:
• Add new TODO items by providing a title
• List all your TODO items
• Mark TODO items as completed by ID
• Delete TODO items by ID

**Example prompts to try:**
• "Add a new TODO: Buy groceries"
• "Show me all my TODO items"
• "Mark TODO item 1 as completed"
• "Delete TODO item 2"

**Available TODO operations:**
• `add_todo_prompt` - Add a new TODO item
• `list_todos_prompt` - List all TODO items
• `complete_todo_prompt` - Mark a TODO as completed
• `delete_todo_prompt` - Delete a TODO item

Just tell me what you'd like to do with your TODOs!"""
            
            ai = AIMessage(content=content)
            return {"messages": [ai]}

        # Create tool node for TODO tools
        tool_node = ToolNode(todo_tools)
        
        # Router function
        def should_call_tool(state: State) -> str:
            last_message = state["messages"][-1]
            return "tools" if getattr(last_message, "tool_calls", None) else "info"

        graph = StateGraph(State)
        graph.add_node("chat", chat_node)
        graph.add_node("tools", tool_node)
        graph.add_node("info", todo_info_node)
        
        graph.add_edge(START, "chat")
        graph.add_conditional_edges("chat", should_call_tool, {"tools": "tools", "info": "info"})
        graph.add_edge("tools", "chat")  # Loop back for follow-up
        graph.add_edge("info", END)
        
        return graph
    except Exception as e:
        from framework.log_service import log
        log(f"Error building 08-todo-app graph: {e}")
        return None