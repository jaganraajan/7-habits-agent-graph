from operator import add
from typing import Annotated, TypedDict, Optional
from langchain_core.messages import AIMessage, BaseMessage, SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.types import Send

from framework.prompt_manager import get_prompt
from framework.decorators import registered_graph
from tools.search_web import search_web
from tools.get_current_datetime import get_current_datetime
from framework.log_service import log
from datetime import datetime

PROMPT_KEY = "04_deep_research"
WORKERS = 5

class SearchTerms(BaseModel):
    terms: list[str] = Field(..., min_items=WORKERS, max_items=WORKERS, description="Various search terms about the main topic.")

class Synthesis(BaseModel):
    text: str = Field(..., description="Results of the searches, summarized in one coherent text.")

class State(TypedDict, total=False):
    initial_term: str
    search_terms: list[str]                              # simple list for fanout
    search_results: Annotated[list[str], add]            # fan-in via list reducer
    messages: Annotated[list[BaseMessage], add_messages]

def init_state() -> State:
    system_prompt = get_prompt(PROMPT_KEY)
    system_prompt += f"\n Limit you terms to {WORKERS} specific search terms to look up."
    system_prompt += f"\n The current date and time is: {datetime.now().isoformat()}."
    return {"messages": [SystemMessage(content=system_prompt)]}

@registered_graph("04-deep-research")
def build_graph():
    try:
        llm_no_tools = ChatOpenAI(model="gpt-4o-mini")
        term_planner = llm_no_tools.with_structured_output(SearchTerms)
        synthesizer_llm = llm_no_tools.with_structured_output(Synthesis)

        # Orchestrator: generate up to WORKERS terms
        def plan_terms(state: State, config: RunnableConfig) -> State:
            initial_term = state.get("messages", [])[-1]
            planned: SearchTerms = term_planner.invoke(state.get("messages", []), config=config)
            return {"search_terms": planned.terms, "initial_term": initial_term.content}

        # Worker: run a single search term; writes to reduced key
        class WorkerState(TypedDict):
            term: str
            search_results: Annotated[list[str], add]

        def search_worker(wstate: WorkerState, config: RunnableConfig) -> WorkerState:
            term = wstate["term"]
            r = search_web(term) 
            return {"search_results": [f"{term}: {r}"]}

        # After workers complete, synthesize
        def synthesize(state: State, config: RunnableConfig) -> State:
            topic = state.get("initial_term", "")
            notes = "\n".join(state.get("search_results", []))
            prompt = ( get_prompt(PROMPT_KEY + "_synthesize") +
                f"Topic: {topic}\n\nSearch Results:\n{notes}"
            )
            syn: Synthesis = synthesizer_llm.invoke(prompt, config=config)
            return {"messages": [AIMessage(content=syn.text)]}

        # Conditional edge that dynamically fans out workers
        def assign_workers(state: State):
            return [Send("search_worker", {"term": t}) for t in state["search_terms"]]

        graph = StateGraph(State)
        graph.add_node("plan_terms", plan_terms)
        graph.add_node("search_worker", search_worker)
        graph.add_node("synthesize", synthesize)

        graph.add_edge(START, "plan_terms")
        graph.add_conditional_edges("plan_terms", assign_workers, ["search_worker"])  # dynamic fan-out
        graph.add_edge("search_worker", "synthesize")                                 # fan-in on reducer
        graph.add_edge("synthesize", END)

        return graph
    except Exception as e:
        log(f"Error building graph: {e}")
        return None
