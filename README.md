# Workshop on LangGraph & LangFuse

In this workshop, we'll be looking at a simple LangGraph & Langfuse integration example. We'll touch on basic agents, patterns and observability.

## Requirements

### Install the dependencies

```bash
uv sync
```

### Activate Virtual Environment

Before running any of the Python scripts, activate the virtual environment:

```bash
source .venv/bin/activate
```

### Install the LangFuse Docker Compose

```bash
git clone git@github.com:langfuse/langfuse.git
cd langfuse
docker-compose up
```

- Connect to the LangFuse UI at [http://localhost:3000](http://localhost:3000).
- Sign up for a new account.
- Create an organisation & a new project.

### Quick Setup: Environment Files

Now that LangFuse is running, you need to configure your environment variables for the workshop steps. Start by copying the example env and setup the proper environement variables. 

```bash
cp .env.example .env
```

### Environment Variables: What You Need

Here is a breakdown of the variables needed for the workshop. 

- `LANGFUSE_PUBLIC_KEY` – Your LangFuse project's public API key.
- `LANGFUSE_SECRET_KEY` – Your LangFuse project's secret API key.
- `LANGFUSE_HOST` – The URL of your LangFuse instance (e.g., `http://localhost:3000` for local Docker).
- `OPENAI_API_KEY`

## References

- [LangGraph](https://github.com/langchain-ai/langgraph)
- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)
- [LangFuse](https://github.com/langfuse/langfuse)
- [LangFuse Docs](https://langfuse.com/docs)