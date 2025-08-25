from datetime import datetime
from langchain_core.tools import tool

# Define tool with decorator
@tool
def get_current_datetime() -> str:
    """Returns the current date and time in ISO format."""
    return datetime.now().isoformat()
