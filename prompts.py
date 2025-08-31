# prompts.py - Exported TODO app prompts for MCP integration

prompts = [
    { 
        "id": "add_todo_prompt", 
        "label": "Add TODO", 
        "description": "Provide a title for the new TODO item.", 
        "inputExample": {"title": "Buy groceries"} 
    },
    { 
        "id": "list_todos_prompt", 
        "label": "List TODOs", 
        "description": "Retrieve the list of all TODO items.", 
        "inputExample": {} 
    },
    { 
        "id": "complete_todo_prompt", 
        "label": "Complete TODO", 
        "description": "Mark a TODO item as completed by providing its ID.", 
        "inputExample": {"id": 1} 
    },
    { 
        "id": "delete_todo_prompt", 
        "label": "Delete TODO", 
        "description": "Delete a TODO item by providing its ID.", 
        "inputExample": {"id": 1} 
    }
]