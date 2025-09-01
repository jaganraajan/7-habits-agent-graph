#!/usr/bin/env python3
"""
Flask-based Web UI for 7 Habits Agent Graph

Provides a web interface with:
1. Vision board images slideshow from data/ folder
2. Chat interface using the 02-tooluse agent graph
"""

import os
import asyncio
import uuid
from pathlib import Path
from typing import List, Dict, Any
from flask import Flask, render_template, request, jsonify, send_from_directory
from datetime import datetime
import json

# Import existing framework components
from framework.graph_manager import invoke_graph
from framework.mcp_registry import init_mcp_registry
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

# Configuration
DATA_DIR = Path(os.getenv("DATA_DIR", "./data")).resolve()
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Global state for chat sessions
chat_sessions: Dict[str, Dict[str, Any]] = {}

def get_image_files() -> List[Dict[str, Any]]:
    """Get all image files from data directory with metadata."""
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    images = []
    
    if not DATA_DIR.exists():
        return images
    
    for file_path in DATA_DIR.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in image_extensions:
            try:
                stat = file_path.stat()
                images.append({
                    'filename': file_path.name,
                    'path': str(file_path.relative_to(DATA_DIR.parent)),
                    'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'size': stat.st_size
                })
            except (OSError, ValueError):
                continue
    
    # Sort by creation time, newest first
    images.sort(key=lambda x: x['created'], reverse=True)
    return images

@app.route('/')
def index():
    """Main page with vision board and chat interface."""
    images = get_image_files()
    return render_template('index.html', images=images)

@app.route('/api/images')
def api_images():
    """API endpoint to get image list."""
    images = get_image_files()
    return jsonify({'images': images})

@app.route('/data/<path:filename>')
def serve_image(filename):
    """Serve images from data directory."""
    return send_from_directory(DATA_DIR, filename)

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """Handle chat requests."""
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'Message is required'}), 400
        
        message = data['message'].strip()
        if not message:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        session_id = data.get('session_id')
        if not session_id:
            session_id = str(uuid.uuid4())
            chat_sessions[session_id] = {
                'thread_id': str(uuid.uuid4()),
                'is_new_thread': True,
                'messages': []
            }
        
        session = chat_sessions.get(session_id)
        if not session:
            session = {
                'thread_id': str(uuid.uuid4()),
                'is_new_thread': True,
                'messages': []
            }
            chat_sessions[session_id] = session
        
        # Add user message to session
        session['messages'].append({
            'type': 'user',
            'content': message,
            'timestamp': datetime.now().isoformat()
        })
        
        # Process message through the 02-tooluse graph
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                response = loop.run_until_complete(
                    invoke_graph(
                        graph_name='02-tooluse',
                        message=message,
                        thread_id=session['thread_id'],
                        is_new_thread=session['is_new_thread']
                    )
                )
            finally:
                loop.close()
        except Exception as graph_error:
            # Fallback response when graph is not available
            print(f"Graph error: {graph_error}")
            if 'add image' in message.lower() or 'generate' in message.lower() or 'create' in message.lower():
                response = "I understand you'd like to create a vision board image. However, the image generation service is currently not configured. Please set up your Azure OpenAI DALL-E credentials in the .env file to enable this feature."
            else:
                response = f"I'm sorry, but I'm currently unable to process your request due to a service configuration issue. The AI agent requires proper setup of external services. Error: {str(graph_error)}"
        
        # Mark session as no longer new
        session['is_new_thread'] = False
        
        # Add assistant response to session
        session['messages'].append({
            'type': 'assistant',
            'content': response,
            'timestamp': datetime.now().isoformat()
        })
        
        return jsonify({
            'response': response,
            'session_id': session_id,
            'message_count': len(session['messages'])
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to process message: {str(e)}'}), 500

@app.route('/api/chat/new', methods=['POST'])
def api_new_chat():
    """Start a new chat session."""
    session_id = str(uuid.uuid4())
    chat_sessions[session_id] = {
        'thread_id': str(uuid.uuid4()),
        'is_new_thread': True,
        'messages': []
    }
    return jsonify({'session_id': session_id})

@app.route('/api/chat/history/<session_id>')
def api_chat_history(session_id):
    """Get chat history for a session."""
    session = chat_sessions.get(session_id)
    if not session:
        return jsonify({'error': 'Session not found'}), 404
    
    return jsonify({
        'session_id': session_id,
        'messages': session['messages']
    })

async def init_app():
    """Initialize the application."""
    try:
        await init_mcp_registry()
        print("MCP registry initialized successfully")
    except Exception as e:
        print(f"Warning: Failed to initialize MCP registry: {e}")
        print("Some features may not be available")

def create_app():
    """Create and configure the Flask app."""
    # Initialize async components
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(init_app())
    finally:
        loop.close()
    
    return app

if __name__ == '__main__':
    # Initialize and run the app
    app = create_app()
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    print(f"Starting Flask app on http://localhost:{port}")
    print(f"Vision board data directory: {DATA_DIR}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)