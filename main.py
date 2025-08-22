import os
import sys
from dotenv import load_dotenv
from framework.chat_app import run_chat_app


def main() -> None:
    load_dotenv()
    run_chat_app()


if __name__ == "__main__":      
    main()