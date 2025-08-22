from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END


def build_graph() -> StateGraph:
    """Linear chat workflow - responds directly to user messages."""
    
    def start_node(state: Dict[str, Any]) -> Dict[str, Any]:
        """Entry point of the graph - passes state through unchanged."""
        return state

    def chat_node(state: Dict[str, Any]) -> Dict[str, Any]:
        """Chat node that responds to user input conversationally."""
        user_message = state.get("user_message", "Hello")
        
        prompt = ChatPromptTemplate.from_template(
            "You are a helpful assistant. Respond to the user's message in a friendly way.\n"
            "User: {message}"
        )
        llm = ChatOpenAI(model="gpt-4o-mini")
        chain = prompt | llm
        callbacks = state.get("callbacks", [])
        
        config = {"callbacks": callbacks} if callbacks else {}
        result = chain.invoke({"message": user_message}, config=config)
        
        return {**state, "response": getattr(result, "content", str(result))}

    # Build the linear graph
    graph = StateGraph(dict)
    graph.add_node("start", start_node)
    graph.add_node("chat", chat_node)
    graph.set_entry_point("start")
    graph.add_edge("start", "chat")
    graph.add_edge("chat", END)
    
    return graph
