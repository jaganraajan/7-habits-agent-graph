import os
import sys
from dotenv import load_dotenv
from framework.chat_app import run_chat_app


def log_loaded_configs() -> None:
    """Log all loaded configuration values."""
    print("=== Loaded Configuration ===")
    
    # Core required configs
    openai_key = os.getenv("OPENAI_API_KEY")
    print(f"OPENAI_API_KEY: {'✓ Set' if openai_key else '✗ Missing'}")
    
    # Langfuse configs
    langfuse_public = os.getenv("LANGFUSE_PUBLIC_KEY")
    langfuse_secret = os.getenv("LANGFUSE_SECRET_KEY") 
    langfuse_host = os.getenv("LANGFUSE_HOST", "http://localhost:3000")
    
    print(f"LANGFUSE_PUBLIC_KEY: {'✓ Set' if langfuse_public else '✗ Missing'}")
    print(f"LANGFUSE_SECRET_KEY: {'✓ Set' if langfuse_secret else '✗ Missing'}")
    print(f"LANGFUSE_HOST: {langfuse_host}")
    
    print("=============================\n")


def main() -> None:
    """Main entry point - launches the Textual chat app."""
    load_dotenv()
    log_loaded_configs()
    
    # Check for required OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY is required!")
        print("Please set it in your environment or .env file.")
        sys.exit(1)
    
    print("🚀 Starting LangGraph Chat Workshop...")
    print("Press Ctrl+C or Ctrl+Q to quit the app.\n")
    
    # Launch the Textual chat app
    run_chat_app()


if __name__ == "__main__":
    main()