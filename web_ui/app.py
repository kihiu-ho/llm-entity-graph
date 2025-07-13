#!/usr/bin/env python3
"""
Web UI for Agentic RAG with Knowledge Graph.

This web application provides a user-friendly interface for the CLI functionality.
"""

import os
import json
import asyncio
import tempfile
import shutil
import threading
import queue
import time
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
import logging

# Try to import required packages with graceful fallback
try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    print("⚠️  aiohttp not available. Install with: pip install aiohttp")

try:
    from flask import Flask, render_template, request, jsonify, Response, stream_template
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    print("❌ Flask not available. Install with: pip install Flask")
    exit(1)

try:
    from flask_cors import CORS
    CORS_AVAILABLE = True
except ImportError:
    CORS_AVAILABLE = False
    print("⚠️  Flask-CORS not available. Install with: pip install Flask-CORS")

try:
    from werkzeug.utils import secure_filename
    WERKZEUG_AVAILABLE = True
except ImportError:
    WERKZEUG_AVAILABLE = False
    print("⚠️  Werkzeug not available. Install with: pip install Werkzeug")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
if CORS_AVAILABLE:
    CORS(app)
else:
    # Basic CORS headers manually
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response

# Configuration
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8058')
WEB_UI_PORT = int(os.getenv('WEB_UI_PORT', 5000))
WEB_UI_HOST = os.getenv('WEB_UI_HOST', '0.0.0.0')

class WebUIClient:
    """Client for communicating with the Agentic RAG API."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')

    async def check_health(self) -> Dict[str, Any]:
        """Check API health status."""
        if not AIOHTTP_AVAILABLE:
            return {
                "status": "unhealthy",
                "error": "aiohttp not available - install with: pip install aiohttp",
                "suggestion": "Run: pip install aiohttp"
            }

        try:
            timeout = aiohttp.ClientTimeout(total=5)  # 5 second timeout
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{self.base_url}/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "status": "healthy",
                            "api_url": self.base_url,
                            **data
                        }
                    else:
                        return {
                            "status": "unhealthy",
                            "error": f"API returned HTTP {response.status}",
                            "api_url": self.base_url,
                            "suggestion": "Check if the API server is running properly"
                        }
        except aiohttp.ClientConnectorError as e:
            return {
                "status": "unhealthy",
                "error": "Cannot connect to API server",
                "api_url": self.base_url,
                "suggestion": "Make sure the Agentic RAG API server is running",
                "details": f"Connection failed: {str(e)}"
            }
        except asyncio.TimeoutError:
            return {
                "status": "unhealthy",
                "error": "Connection timeout",
                "api_url": self.base_url,
                "suggestion": "API server is not responding - check if it's running",
                "details": "Request timed out after 5 seconds"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": f"Unexpected error: {str(e)}",
                "api_url": self.base_url,
                "suggestion": "Check API server status and configuration"
            }
    
    async def stream_chat(self, message: str, session_id: Optional[str] = None, user_id: str = "web_user"):
        """Stream chat response from API."""
        if not AIOHTTP_AVAILABLE:
            yield {
                "type": "error",
                "content": "aiohttp not available - install with: pip install aiohttp"
            }
            return

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
    loop = None
    try:
        # Create a new event loop for this request
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def get_health():
            return await client.check_health()

        # Run async function with timeout
        health_data = loop.run_until_complete(
            asyncio.wait_for(get_health(), timeout=10.0)
        )
        return jsonify(health_data)
    except asyncio.TimeoutError:
        return jsonify({"status": "error", "message": "Health check timeout"}), 503
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 503
    finally:
        if loop:
            try:
                # Clean up any remaining tasks
                pending = asyncio.all_tasks(loop)
                for task in pending:
                    task.cancel()
                if pending:
                    loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                loop.close()
            except Exception as e:
                logger.warning(f"Error closing event loop: {e}")

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
        """Generate streaming response using thread-based approach."""
        chunk_queue = queue.Queue()
        error_occurred = threading.Event()

        def async_worker():
            """Worker thread to handle async operations."""
            try:
                # Create event loop in this thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                async def stream_chunks():
                    try:
                        async for chunk in client.stream_chat(message, session_id, user_id):
                            chunk_queue.put(f"data: {json.dumps(chunk)}\n\n")
                    except Exception as e:
                        logger.error(f"Streaming error: {e}")
                        chunk_queue.put(f"data: {json.dumps({'error': str(e), 'type': 'error'})}\n\n")
                        error_occurred.set()
                    finally:
                        chunk_queue.put(None)  # Signal end of stream

                # Run the async function
                loop.run_until_complete(stream_chunks())

            except Exception as e:
                logger.error(f"Worker thread error: {e}")
                chunk_queue.put(f"data: {json.dumps({'error': str(e), 'type': 'error'})}\n\n")
                chunk_queue.put(None)
                error_occurred.set()
            finally:
                try:
                    loop.close()
                except:
                    pass

        # Start the worker thread
        worker = threading.Thread(target=async_worker, daemon=True)
        worker.start()

        # Yield chunks as they become available
        try:
            while True:
                try:
                    # Get chunk with timeout to avoid hanging
                    chunk = chunk_queue.get(timeout=30)
                    if chunk is None:  # End of stream
                        break
                    yield chunk
                except queue.Empty:
                    # Timeout occurred, check if worker is still alive
                    if not worker.is_alive():
                        logger.error("Worker thread died unexpectedly")
                        yield f"data: {json.dumps({'error': 'Stream timeout', 'type': 'error'})}\n\n"
                        break
                    # Send keepalive
                    yield f"data: {json.dumps({'type': 'keepalive'})}\n\n"
        except Exception as e:
            logger.error(f"Generator error: {e}")
            yield f"data: {json.dumps({'error': str(e), 'type': 'error'})}\n\n"

    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type'
        }
    )



@app.route('/documents')
def documents():
    """List available documents."""
    limit = request.args.get('limit', 20, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    async def get_documents():
        if not AIOHTTP_AVAILABLE:
            return {"error": "aiohttp not available - install with: pip install aiohttp"}

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
