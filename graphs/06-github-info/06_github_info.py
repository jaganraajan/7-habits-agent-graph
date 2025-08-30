
from typing import Annotated, TypedDict
from langchain_core.messages import AIMessage, BaseMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from framework.decorators import registered_graph
from langchain_mcp_adapters.client import MCPClient

# this is the key for the prompt in the prompt manager which gets the Langfuse prompt
PROMPT_KEY = "06_github_info"

# the state that will be passed to each node
class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def init_state() -> State:
    # Optionally, you can add a SystemMessage or leave empty
    return {"messages": []}

@registered_graph("06-github-info")
def build_graph() -> StateGraph:
    async def github_info_node(state: State, config: RunnableConfig) -> State:
        owner = state.get("owner", "jaganraajan")
        repo_name = state.get("repo", "7-habits-agent-graph")
        mcp = MCPClient(server_name="github")
        params = {"owner": owner, "repo": repo_name, "per_page": 5}
        result = await mcp.call_tool("get_commits", params)
        commits = result.get("commits", [])
        if not commits:
            content = f"No commits found for {owner}/{repo_name}."
        else:
            content = f"Latest commits for {owner}/{repo_name}:\n"
            for commit in commits:
                content += f"- {commit['message']} by {commit['author']} (SHA: {commit['sha']})\n"
        ai = AIMessage(content=content)
        return {"messages": [ai]}

    graph = StateGraph(State)
    graph.add_node("github_info", github_info_node)
    graph.add_edge(START, "github_info")
    graph.add_edge("github_info", END)
    return graph