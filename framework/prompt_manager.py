import os
from dotenv import load_dotenv
from langfuse import Langfuse

load_dotenv()

# Initialize Langfuse only if credentials are available
langfuse = None
if os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"):
    try:
        langfuse = Langfuse(
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            host=os.getenv("LANGFUSE_HOST"),
        )
    except Exception:
        langfuse = None

def get_prompt(name: str, label: str = "production") -> str:
    """Get prompt from Langfuse or return None if not available."""
    if langfuse is None:
        return None
    
    try:
        return langfuse.get_prompt(name, label=label).prompt
    except Exception:
        return None