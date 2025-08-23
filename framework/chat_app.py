import asyncio
import os
import uuid
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

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from workflows.graph_registry import registry       
from framework.graph_manager import invoke_graph, build_graph


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
        options = [(graph.name, graph.name) for graph in graphs]
        
        if not options:
            options = [("none", "No workflows found")]
        
        yield Select(options, id="graph_select")


class ChatInterface(Container):
    """Main chat interface."""
    
    current_graph = reactive(None)
    current_thread_id = reactive(None)
    
    def compose(self) -> ComposeResult:
        with Vertical():
            yield GraphSelector()
            yield RichLog(id="chat_log", markup=True, wrap=True)
            with Horizontal(classes="input-area"):
                yield Input(placeholder="Type your message and press Enter...", id="message_input", classes="input-container")
                yield Button("New Thread", id="new_thread_btn", classes="new-thread-btn")
    
    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle graph selection change."""
        if event.control.id == "graph_select":
            self.current_graph = event.value
                
            # Generate new thread ID for the selected graph
            self.current_thread_id = str(uuid.uuid4())
                
            chat_log = self.query_one("#chat_log", RichLog)
            chat_log.clear()
            
            if self.current_graph and self.current_graph != "none":
                chat_log.write(f"[bold green]Switched to workflow: {self.current_graph}[/bold green]")
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission (Enter key)."""
        if event.input.id == "message_input":
            self.send_message()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "new_thread_btn":
            self.start_new_thread()
    
    def start_new_thread(self) -> None:
        """Start a new conversation thread."""
        if not self.current_graph or self.current_graph == "none":
            chat_log = self.query_one("#chat_log", RichLog)
            chat_log.write("[bold red]Please select a workflow first![/bold red]")
            return
        
        # Generate new thread ID
        self.current_thread_id = str(uuid.uuid4())
        
        # Clear chat log
        chat_log = self.query_one("#chat_log", RichLog)
        chat_log.clear()
        
        # Show new thread started message
        chat_log.write("[bold green]🔄 New conversation thread started![/bold green]")
    
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
            
            graph = build_graph(self.current_graph)

            # Run the graph using graph_manager with thread_id
            result = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: invoke_graph(
                    graph,
                    {"user_message": message},
                    self.current_thread_id
                )
            )
            
            # Display response
            response = result.get("messages", [])
            if response:
                response = response[-1].content
            else:
                response = "No response generated"

            chat_log.write(f"[bold green]🤖 Assistant:[/bold green] {response}")


            
        except Exception as e:
            chat_log.write(f"[bold red]Error:[/bold red] {str(e)}")

    
class ChatApp(App):
    """Main chat application."""
    
    CSS = """
    /* Global styles */
    Screen {
        background: $surface;
    }
    
    /* Header - consistent spacing */
    Header {
        margin: 0 0 1 0;
        padding: 0;
    }
    
    /* Main layout containers */
    ChatInterface {
        padding: 0 1 1 1;
    }
    
    /* Workflow selector section */
    GraphSelector {
        height: auto;
        margin: 0 0 1 0;
    }
    
    .label {
        margin: 0;
        text-style: bold;
    }
    
    /* Chat log area */
    #chat_log {
        height: 1fr;
        border: solid $primary;
        margin: 0 0 1 0;
        overflow-x: hidden;
        overflow-y: auto;
        scrollbar-size: 1 1;
    }
    
    /* Input area container */
    .input-area {
        height: auto;
        margin: 0;
        padding: 0;
    }
    
    /* Input field */
    .input-container {
        height: 3;
        width: 1fr;
        margin: 0;
        overflow-y: auto;
    }
    
    /* New thread button */
    .new-thread-btn {
        width: 15;
        height: 3;
        margin: 0 0 0 1;
        background: $primary;
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
