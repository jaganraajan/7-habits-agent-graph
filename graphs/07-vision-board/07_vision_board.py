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
from framework.prompt_manager import get_prompt
from framework.mcp_registry import get_mcp_tools
from tools.generate_vision_image import generate_vision_image

# this is the key for the prompt in the prompt manager which gets the Langfuse prompt
PROMPT_KEY = "07_vision_board"

# the state that will be passed to each node
class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def init_state() -> State:
    system_prompt = get_prompt(PROMPT_KEY)
    return {"messages": [SystemMessage(content=system_prompt)]}

@registered_graph("07-vision-board")
def build_graph() -> StateGraph:
    load_dotenv()
    try:
        # Get vision MCP tools and combine with direct tool
        vision_mcp_tools = get_mcp_tools("vision")
        direct_tools = [generate_vision_image]
        
        # Combine MCP tools with direct tools
        all_vision_tools = [*vision_mcp_tools, *direct_tools]
        
        def chat_node(state: State, config: RunnableConfig) -> State:
            subscription_key = os.getenv("AZURE_OPENAI_API_KEY")
            api_version = "2024-12-01-preview"

            # Initialize LLM with vision tools
            llm = AzureChatOpenAI(
                api_key=subscription_key,
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_version=api_version,
                deployment_name="gpt-4o-mini"
            ).bind_tools(all_vision_tools)
            
            ai: AIMessage = llm.invoke(state["messages"], config=config)
            return {"messages": [ai]}

        def vision_info_node(state: State, config: RunnableConfig) -> State:
            # Create a helpful introduction message about vision board capabilities
            content = """I can help you create vision board images using Azure OpenAI DALL-E! 

Here's what I can do:
• Generate inspiring vision board images from your text descriptions
• Create images in different sizes (1024x1024, 1792x1024, 1024x1792)
• Save images locally for easy frontend integration
• Provide both vision text and image URLs

**Example prompts to try:**
• "Create a vision board showing career success with a corner office, certificates, and achievements"
• "Generate an image representing health and fitness goals with running, healthy food, and strength"
• "Design a vision for travel dreams with beautiful destinations, airplanes, and adventure scenes"
• "Create a family and relationship vision with happy moments, love, and togetherness"

**Available tools:**
• `generate_vision_image` - Direct tool for quick image generation
• `vision/add_with_image` - MCP tool for vision board entries with metadata

Just describe your vision and I'll generate a beautiful image to represent it!"""
            
            ai = AIMessage(content=content)
            return {"messages": [ai]}

        # Create tool node for vision tools
        tool_node = ToolNode(all_vision_tools)
        
        # Router function
        def should_call_tool(state: State) -> str:
            last_message = state["messages"][-1]
            return "tools" if getattr(last_message, "tool_calls", None) else "info"

        # Build the graph
        graph = StateGraph(State)
        graph.add_node("chat", chat_node)
        graph.add_node("tools", tool_node)
        graph.add_node("info", vision_info_node)
        
        graph.add_edge(START, "chat")
        graph.add_conditional_edges("chat", should_call_tool, {"tools": "tools", "info": "info"})
        graph.add_edge("tools", "chat")  # Loop back for follow-up
        graph.add_edge("info", END)
        
        return graph
    except Exception as e:
        from framework.log_service import log
        log(f"Error building 07-vision-board graph: {e}")
        return None