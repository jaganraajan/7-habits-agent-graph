"""Textual-based chat application for LangGraph workflows."""

import asyncio
import os
from typing import Optional
from dotenv import load_dotenv
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import (
    Header, Footer, Input, Button, Static, Select, 
    RichLog, LoadingIndicator
)
from textual.message import Message
from textual.reactive import reactive
from langfuse.langchain import CallbackHandler
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from workflows.workflow_registry import registry

# Ensure environment is loaded
load_dotenv()


class ChatMessage(Static):
    """A chat message widget."""
    
    def __init__(self, content: str, is_user: bool = False):
        self.is_user = is_user
        prefix = "🧑 You: " if is_user else "🤖 Assistant: "
        super().__init__(f"{prefix}{content}")
        self.add_class("user-message" if is_user else "assistant-message")


class GraphSelector(Container):
    """Widget for selecting which graph to use."""
    
    def compose(self) -> ComposeResult:
        yield Static("Select Workflow:", classes="label")
        
        # Get available graphs
        graphs = registry.list_graphs()
        options = [(graph.name, f"{graph.name}: {graph.description}") for graph in graphs]
        
        if not options:
            options = [("none", "No workflows found")]
        
        yield Select(options, id="graph_select")


class ChatInterface(Container):
    """Main chat interface."""
    
    current_graph = reactive(None)
    
    def compose(self) -> ComposeResult:
        with Vertical():
            yield GraphSelector()
            yield RichLog(id="chat_log", markup=True, wrap=True)
            yield Input(placeholder="Type your message and press Enter...", id="message_input", classes="input-container")
    
    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle graph selection change."""
        if event.control.id == "graph_select":
            # Extract just the workflow name (before the colon)
            if event.value and ":" in event.value:
                self.current_graph = event.value.split(":")[0].strip()
            else:
                self.current_graph = event.value
                
            chat_log = self.query_one("#chat_log", RichLog)
            chat_log.clear()
            
            if self.current_graph and self.current_graph != "none":
                chat_log.write(f"[bold green]Switched to workflow: {event.value}[/bold green]")
                chat_log.write("[dim]You can now start chatting![/dim]")
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission (Enter key)."""
        if event.input.id == "message_input":
            self.send_message()
    
    def send_message(self) -> None:
        """Send the current message."""
        message_input = self.query_one("#message_input", Input)
        message = message_input.value.strip()
        
        if not message:
            return
        
        if not self.current_graph or self.current_graph == "none":
            chat_log = self.query_one("#chat_log", RichLog)
            chat_log.write("[bold red]Please select a workflow first![/bold red]")
            return
        
        # Clear input
        message_input.value = ""
        
        # Show user message
        chat_log = self.query_one("#chat_log", RichLog)
        chat_log.write(f"[bold blue]🧑 You:[/bold blue] {message}")
        
        # Process message asynchronously
        self.run_worker(self.process_message(message), exclusive=True)
    
    async def process_message(self, message: str) -> None:
        """Process the message through the selected graph."""
        chat_log = self.query_one("#chat_log", RichLog)
        
        try:
            # Show thinking indicator
            chat_log.write("[dim]🤖 Assistant is thinking...[/dim]")
            
            # Get the graph
            try:
                graph = registry.build_graph(self.current_graph)
                if not graph:
                    chat_log.write(f"[bold red]Error: Could not build graph for '{self.current_graph}'![/bold red]")
                    return
            except Exception as e:
                chat_log.write(f"[bold red]Error building graph: {str(e)}[/bold red]")
                return
            
            # Set up Langfuse callback if available
            try:
                langfuse_handler = CallbackHandler()
                callbacks = [langfuse_handler]
            except Exception:
                callbacks = []
            
            # Run the graph
            result = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: graph.invoke({
                    "user_message": message,
                    "callbacks": callbacks
                })
            )
            
            # Display response
            response = result.get("response", "No response generated")
            chat_log.write(f"[bold green]🤖 Assistant:[/bold green] {response}")
            
        except Exception as e:
            chat_log.write(f"[bold red]Error:[/bold red] {str(e)}")


class ChatApp(App):
    """Main chat application."""
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    .label {
        margin: 1 0;
        text-style: bold;
    }
    
    #chat_log {
        height: 1fr;
        border: solid $primary;
        margin: 1 0;
        overflow-x: hidden;
    }
    
    .input-container {
        height: auto;
        margin: 1 0;
    }
    
    GraphSelector {
        height: auto;
        margin: 1 0;
    }
    """
    
    BINDINGS = [
        ("ctrl+c", "quit", "Quit"),
        ("ctrl+q", "quit", "Quit"),
    ]
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield ChatInterface()
        yield Footer()
    
    def on_mount(self) -> None:
        """Called when app starts."""
        self.title = "LangGraph Chat Workshop"
        self.sub_title = "Interactive AI Chat with Multiple Workflows"


def run_chat_app():
    """Run the chat application."""
    app = ChatApp()
    app.run()
