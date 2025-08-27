from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

from framework.prompt_manager import get_prompt
from framework.decorators import registered_graph

# this is the key for the prompt in the prompt manager which gets the Langfuse prompt
PROMPT_KEY = "01_linear"

# the state that will be passed to each node
class State(TypedDict):
    # List of messages, with add_messages to handle history (adds to the list)
    messages: Annotated[list[BaseMessage], add_messages]

def init_state() -> State:
    system_prompt = get_prompt(PROMPT_KEY)
    return {"messages": [SystemMessage(content=system_prompt)]}

@registered_graph("01-linear")
def build_graph() -> StateGraph:
    
    def chat_node(state: State, config: RunnableConfig) -> State:
        # Initialize LLM
        llm = ChatOpenAI(model="gpt-4o-mini")
        
        # Invoke LLM with all messages from state (add_messages handles history)
        ai: AIMessage = llm.invoke(state["messages"], config=config)
        
        # Return only the AI response; add_messages will append it
        return {"messages": [ai]}


    # initialize graph
    graph = StateGraph(State)

    # add node
    graph.add_node("chat", chat_node)
    
    # add edges
    graph.add_edge(START, "chat")
    graph.add_edge("chat", END)
    
    return graph
