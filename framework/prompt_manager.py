import os
from typing import Optional
from dotenv import load_dotenv
from langfuse import Langfuse

load_dotenv()

class PromptManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.langfuse = Langfuse(
                public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
                secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
                host=os.getenv("LANGFUSE_HOST")
            )
            self._initialized = True
    
    def get_prompt(self, name: str, label: str = "production") -> str:
        """Get a prompt string from Langfuse by name and label."""
        prompt = self.langfuse.get_prompt(name, label=label)
        return prompt.prompt
    
    def get_production_prompt(self, name: str) -> str:
        """Get a prompt string with the 'production' label."""
        return self.get_prompt(name, label="production")

prompt_manager = PromptManager()