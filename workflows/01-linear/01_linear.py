from typing import Dict, Any, TypedDict, Annotated
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END, START      
from framework.prompt_manager import prompt_manager
from langchain_core.messages import BaseMessage
from operator import add

PROMPT_KEY = "persona"

# the state that will be passed to each node
class State(TypedDict):
    user_message: str
    messages: list[BaseMessage]

def build_graph() -> StateGraph:
    
    def chat_node(state: State) -> State:
        # get system prompt
        system_prompt = prompt_manager.get_production_prompt(PROMPT_KEY)
        
        # get existing messages or start with system prompt
        existing_messages = state.get("messages", [])
        
        # ensure system prompt is always first (add it if messages is empty)
        if not existing_messages:
            existing_messages = [SystemMessage(content=system_prompt)]
        
        # add the new user message
        messages = [*existing_messages, HumanMessage(content=state.get("user_message"))]

        # initialize llm
        llm = ChatOpenAI(model="gpt-4o-mini")

        # invoke llm
        result = llm.invoke(messages)
        
        # return response with updated messages including the LLM response
        return {**state, "messages": [*messages, result]}


    # initialize graph
    graph = StateGraph(State)

    # add node
    graph.add_node("chat", chat_node)
    
    # add edges
    graph.add_edge(START, "chat")
    graph.add_edge("chat", END)
    
    return graph
