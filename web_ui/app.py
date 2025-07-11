#!/usr/bin/env python3
"""
Web UI for Agentic RAG with Knowledge Graph.

This web application provides a user-friendly interface for the CLI functionality.
"""

import os
import json
import asyncio
import aiohttp
from datetime import datetime
from typing import Dict, Any, Optional

from flask import Flask, render_template, request, jsonify, Response, stream_template
from flask_cors import CORS
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuration
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8058')
WEB_UI_PORT = int(os.getenv('WEB_UI_PORT', 5001))
WEB_UI_HOST = os.getenv('WEB_UI_HOST', '0.0.0.0')

class WebUIClient:
    """Client for communicating with the Agentic RAG API."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        
    async def check_health(self) -> Dict[str, Any]:
        """Check API health status."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/health") as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return {
                            "status": "unhealthy",
                            "error": f"HTTP {response.status}"
                        }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def stream_chat(self, message: str, session_id: Optional[str] = None, user_id: str = "web_user"):
        """Stream chat response from API."""
        request_data = {
            "message": message,
            "session_id": session_id,
            "user_id": user_id,
            "search_type": "hybrid"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/stream",
                    json=request_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        yield {
                            "type": "error",
                            "content": f"API Error ({response.status}): {error_text}"
                        }
                        return
                    
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        
                        if line.startswith('data: '):
                            try:
                                data = json.loads(line[6:])  # Remove 'data: ' prefix
                                yield data
                            except json.JSONDecodeError:
                                continue
                                
        except Exception as e:
            yield {
                "type": "error",
                "content": f"Connection error: {str(e)}"
            }

# Initialize client
client = WebUIClient(API_BASE_URL)

@app.route('/')
def index():
    """Serve the main chat interface."""
    return render_template('index.html')

@app.route('/health')
def health():
    """Check API health status."""
    async def get_health():
        return await client.check_health()
    
    # Run async function in sync context
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        health_data = loop.run_until_complete(get_health())
        return jsonify(health_data)
    finally:
        loop.close()

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages with streaming response."""
    data = request.get_json()
    message = data.get('message', '')
    session_id = data.get('session_id')
    user_id = data.get('user_id', 'web_user')
    
    if not message:
        return jsonify({"error": "Message is required"}), 400
    
    def generate():
        """Generate streaming response."""
        async def stream_response():
            async for chunk in client.stream_chat(message, session_id, user_id):
                yield f"data: {json.dumps(chunk)}\n\n"
        
        # Run async generator in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            async_gen = stream_response()
            while True:
                try:
                    chunk = loop.run_until_complete(async_gen.__anext__())
                    yield chunk
                except StopAsyncIteration:
                    break
        finally:
            loop.close()
    
    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*'
        }
    )



@app.route('/documents')
def documents():
    """List available documents."""
    limit = request.args.get('limit', 20, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    async def get_documents():
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{API_BASE_URL}/documents",
                    params={"limit": limit, "offset": offset}
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        return {
                            "error": f"Failed to fetch documents ({response.status}): {error_text}"
                        }
        except Exception as e:
            return {"error": f"Document fetch error: {str(e)}"}
    
    # Run async function in sync context
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(get_documents())
        return jsonify(result)
    finally:
        loop.close()

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal error: {error}")
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    print(f"🌐 Starting Web UI for Agentic RAG")
    print(f"📡 API URL: {API_BASE_URL}")
    print(f"🚀 Web UI URL: http://{WEB_UI_HOST}:{WEB_UI_PORT}")
    
    app.run(
        host=WEB_UI_HOST,
        port=WEB_UI_PORT,
        debug=True
    )
