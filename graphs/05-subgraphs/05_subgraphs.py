from operator import add
from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from framework.prompt_manager import get_prompt
from framework.decorators import registered_graph
from framework.mcp_registry import get_mcp_tools
from tools.search_web import search_web
from tools.send_sms import send_sms
from tools.deep_research import deep_research
from framework.log_service import log
from datetime import datetime

PROMPT_KEY = "03_react"


class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def init_state() -> State:
    system_prompt = get_prompt(PROMPT_KEY)
    system_prompt += f"\n The current date and time is: {datetime.now().isoformat()}."
    return {"messages": [SystemMessage(content=system_prompt)]}

class ReasonOut(BaseModel):
    observation: str = Field(..., description="What you saw or received (include any new info from last tool result).")
    suggested_action: str = Field(..., description="One of the available tools or END.")
    reason: str = Field(..., description="Why that action?")

class AnswerOut(BaseModel):
    final_answer: str = Field(..., description="Clear, user-facing answer.")

@registered_graph("05-subgraphs")
def build_graph() -> StateGraph:
    try:
        # Tools
        filesystem_tools = get_mcp_tools("filesystem")
        all_tools = [
            *filesystem_tools,
            send_sms,
            search_web,
            deep_research,
        ]

        tool_text = "\n".join(f"- {t.name}: {t.description}" for t in all_tools)

        # Non-act nodes are tool-blind
        llm_no_tools = ChatOpenAI(model="gpt-4o-mini").bind_tools([], tool_choice="none")

        # Structured LLMs
        reason_llm = llm_no_tools.with_structured_output(ReasonOut)
        answer_llm = llm_no_tools.with_structured_output(AnswerOut)

        # -------- Nodes --------
        def reason_node(state: State, config: RunnableConfig) -> State:
            sys = SystemMessage(content=get_prompt("03_react_reason") + f"\n\nAvailable tools:\n{tool_text}\n")
            out: ReasonOut = reason_llm.invoke(state["messages"] + [sys], config=config)

            content = (
                "REASONING\n"
                f"Observation: {out.observation}\n"
                f"Suggested Action: {out.suggested_action}\n"
                f"Reason: {out.reason}"
            )
            return {"messages": [AIMessage(content=content)]}

        def act_node(state: State, config: RunnableConfig) -> State:
            llm = ChatOpenAI(model="gpt-4o-mini").bind_tools(all_tools)
            ai: AIMessage = llm.invoke(state["messages"], config=config)
            return {"messages": [ai]}

        def answer_node(state: State, config: RunnableConfig) -> State:
            sys = SystemMessage(content=get_prompt("03_react_answer"))
            out: AnswerOut = answer_llm.invoke(state["messages"] + [sys], config=config)
            return {"messages": [AIMessage(content=out.final_answer)]}

        tool_node = ToolNode(all_tools)

        def should_call_tool(state: State) -> str:
            last = state["messages"][-1]
            return "tools" if getattr(last, "tool_calls", None) else "answer"

        graph = StateGraph(State)
        graph.add_node("reason", reason_node)
        graph.add_node("act", act_node)
        graph.add_node("tools", tool_node)
        graph.add_node("answer", answer_node)

        graph.add_edge(START, "reason")
        graph.add_edge("reason", "act")
        graph.add_conditional_edges("act", should_call_tool, {"tools": "tools", "answer": "answer"})
        graph.add_edge("tools", "reason")
        graph.add_edge("answer", END)

        return graph
    except Exception as e:
        log(f"Error building graph: {e}")
        return None