from typing import Dict, Any, TypedDict
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END, START      
from framework.prompt_manager import prompt_manager

PROMPT_KEY = "persona"

# the state that will be passed to each node
class State(TypedDict):
    user_message: str
    response: str

def build_graph() -> StateGraph:
    
    def chat_node(state: State) -> State:

        # get system prompt
        system_prompt = prompt_manager.get_production_prompt(PROMPT_KEY)

        # create messages
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=state.get("user_message"))
        ]

        # initialize llm
        llm = ChatOpenAI(model="gpt-4o-mini")

        # invoke llm
        result = llm.invoke(messages)
        
        # return response
        return {**state, "response": result.content}


    # initialize graph
    graph = StateGraph(State)

    # add node
    graph.add_node("chat", chat_node)
    
    # add edges
    graph.add_edge(START, "chat")
    graph.add_edge("chat", END)
    
    return graph
