from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from framework.graph_registry import registry
from framework.graph_manager import get_compiled_graph

GRAPH_NAME = "04-deep-research"

class DeepResearchArgs(BaseModel):
    query: str = Field(..., description="Topic to investigate deeply.")

@tool("deep_research", args_schema=DeepResearchArgs)
def deep_research(
    query: str,
    config: RunnableConfig, # injected automatically
) -> str:
    """
    Run the deep research subgraph and return a synthesized answer.
    """
    
    # Get the compiled deep research graph
    graph = get_compiled_graph(GRAPH_NAME)
    if not graph:
        return f"Error: Could not load deep research graph"
    
    # Get the graph module for init_state
    graph_module = registry.get_graph_module(GRAPH_NAME)
    if not graph_module:
        return f"Error: Could not load deep research graph module"
    
    try:
        # Initialize the graph state with system prompt
        initial_state = graph_module.init_state()
        
        # Prepare input with the query as a human message
        input_data = {
            "messages": initial_state["messages"] + [HumanMessage(content=query)]
        }
        
        # Run the deep research graph synchronously
        # Note: We use invoke instead of ainvoke since this tool runs in sync context
        result = graph.invoke(input_data, config=config)

        # Extract and return the response message
        response_messages = result.get("messages", [])
        if response_messages:
            return response_messages[-1].content
        else:
            return "No research results generated"
            
    except Exception as e:
        return f"Error running deep research: {str(e)}"
    

# RunnableConfig and InjectedState are injected into the tool at runtime; 
# you don’t expose them to the model, but you can use them to forward callbacks (Langfuse), thread_id, etc., 
# into the subgraph call, so everything is traced as one parent trace with nested spans
