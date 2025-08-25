import os

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_perplexity import ChatPerplexity
from langchain_core.tools import tool

@tool
def search_web(search_term: str) -> str:
    """Search the web using Perplexity's API for real-time information.
    
    Args:
        search_term: The query or topic to search for on the web
    """
    try:
        # Get API key from environment
        api_key = os.getenv("PPLX_API_KEY")
        if not api_key:
            return "Error: PPLX_API_KEY not found in environment variables"
        
        # Initialize ChatPerplexity with real-time web search model
        chat = ChatPerplexity(
            model="sonar",  # Uses real-time web search
            temperature=0.3,  # Lower temperature for more factual responses
            pplx_api_key=api_key
        )
        
        # Create messages for the search
        messages = [
            SystemMessage(content="You are a helpful web search assistant. Provide accurate, up-to-date information based on your web search capabilities."),
            HumanMessage(content=f"Search for and provide information about: {search_term}")
        ]
        
        # Perform the search
        response = chat.invoke(messages)
        
        # Return the content
        return response.content
            
    except Exception as e:
        return f"Error performing web search: {str(e)}"