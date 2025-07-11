#!/usr/bin/env python3
"""
Web UI for Agentic RAG with Knowledge Graph.

This web application provides a user-friendly interface for the CLI functionality.
"""

import os
import json
import asyncio
import aiohttp
import tempfile
import shutil
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

from flask import Flask, render_template, request, jsonify, Response, stream_template
from flask_cors import CORS
from werkzeug.utils import secure_filename
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

@app.route('/api/settings', methods=['GET'])
def get_settings():
    """Get current environment settings."""
    try:
        settings = {
            'database_url': os.getenv('DATABASE_URL', ''),
            'neo4j_uri': os.getenv('NEO4J_URI', ''),
            'neo4j_username': os.getenv('NEO4J_USERNAME', ''),
            'neo4j_password': os.getenv('NEO4J_PASSWORD', ''),
            'llm_provider': os.getenv('LLM_PROVIDER', 'openai'),
            'llm_api_key': os.getenv('LLM_API_KEY', ''),
            'llm_model': os.getenv('LLM_CHOICE', ''),
            'embedding_model': os.getenv('EMBEDDING_MODEL', ''),
            'chunk_size': int(os.getenv('CHUNK_SIZE', 8000)),
            'chunk_overlap': int(os.getenv('CHUNK_OVERLAP', 800)),
            'extract_entities': os.getenv('EXTRACT_ENTITIES', 'true').lower() == 'true',
            'clean_before_ingest': os.getenv('CLEAN_BEFORE_INGEST', 'false').lower() == 'true'
        }
        return jsonify(settings)
    except Exception as e:
        logger.error(f"Failed to get settings: {e}")
        return jsonify({"error": "Failed to get settings"}), 500

@app.route('/api/settings', methods=['POST'])
def save_settings():
    """Save environment settings."""
    try:
        settings = request.get_json()

        # Create or update .env file
        env_file_path = Path(__file__).parent.parent / '.env'

        # Read existing .env file if it exists
        existing_env = {}
        if env_file_path.exists():
            with open(env_file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        existing_env[key] = value

        # Update with new settings
        env_mapping = {
            'database_url': 'DATABASE_URL',
            'neo4j_uri': 'NEO4J_URI',
            'neo4j_username': 'NEO4J_USERNAME',
            'neo4j_password': 'NEO4J_PASSWORD',
            'llm_provider': 'LLM_PROVIDER',
            'llm_api_key': 'LLM_API_KEY',
            'llm_model': 'LLM_CHOICE',
            'embedding_model': 'EMBEDDING_MODEL',
            'chunk_size': 'CHUNK_SIZE',
            'chunk_overlap': 'CHUNK_OVERLAP',
            'extract_entities': 'EXTRACT_ENTITIES',
            'clean_before_ingest': 'CLEAN_BEFORE_INGEST'
        }

        for setting_key, env_key in env_mapping.items():
            if setting_key in settings:
                value = settings[setting_key]
                if isinstance(value, bool):
                    value = 'true' if value else 'false'
                existing_env[env_key] = str(value)

        # Write updated .env file
        with open(env_file_path, 'w') as f:
            for key, value in existing_env.items():
                f.write(f"{key}={value}\n")

        return jsonify({"message": "Settings saved successfully"})

    except Exception as e:
        logger.error(f"Failed to save settings: {e}")
        return jsonify({"error": "Failed to save settings"}), 500

@app.route('/api/test-connections', methods=['POST'])
def test_connections():
    """Test database connections."""
    try:
        data = request.get_json()

        async def test_db_connections():
            # Test PostgreSQL
            db_ok = False
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{API_BASE_URL}/test-db",
                        json={"database_url": data.get('database_url')}
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            db_ok = result.get('success', False)
            except Exception as e:
                logger.error(f"PostgreSQL test failed: {e}")

            # Test Neo4j
            neo4j_ok = False
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{API_BASE_URL}/test-neo4j",
                        json={
                            "neo4j_uri": data.get('neo4j_uri'),
                            "neo4j_username": data.get('neo4j_username'),
                            "neo4j_password": data.get('neo4j_password')
                        }
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            neo4j_ok = result.get('success', False)
            except Exception as e:
                logger.error(f"Neo4j test failed: {e}")

            return {"database": db_ok, "neo4j": neo4j_ok}

        # Run async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(test_db_connections())
            return jsonify(result)
        finally:
            loop.close()

    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return jsonify({"error": "Connection test failed"}), 500

@app.route('/api/test-llm', methods=['POST'])
def test_llm():
    """Test LLM connection."""
    try:
        data = request.get_json()

        async def test_llm_connection():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{API_BASE_URL}/test-llm",
                        json={
                            "provider": data.get('provider'),
                            "api_key": data.get('api_key'),
                            "model": data.get('model')
                        }
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            return result
                        else:
                            return {"success": False, "error": f"HTTP {response.status}"}
            except Exception as e:
                return {"success": False, "error": str(e)}

        # Run async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(test_llm_connection())
            return jsonify(result)
        finally:
            loop.close()

    except Exception as e:
        logger.error(f"LLM test failed: {e}")
        return jsonify({"error": "LLM test failed"}), 500

@app.route('/api/ingest', methods=['POST'])
def ingest_documents():
    """Handle document ingestion with file upload."""
    try:
        # Check if files were uploaded
        if 'files' not in request.files:
            return jsonify({"error": "No files uploaded"}), 400

        files = request.files.getlist('files')
        if not files or all(f.filename == '' for f in files):
            return jsonify({"error": "No files selected"}), 400

        # Get ingestion configuration
        config_str = request.form.get('config', '{}')
        config = json.loads(config_str)

        # Create temporary directory for uploaded files
        temp_dir = tempfile.mkdtemp()

        try:
            # Save uploaded files
            saved_files = []
            for file in files:
                if file.filename and (file.filename.endswith('.md') or file.filename.endswith('.txt')):
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(temp_dir, filename)
                    file.save(file_path)
                    saved_files.append(file_path)

            if not saved_files:
                return jsonify({"error": "No valid files to ingest"}), 400

            # Stream ingestion progress
            def generate_progress():
                try:
                    # Start ingestion via API
                    async def run_ingestion():
                        async with aiohttp.ClientSession() as session:
                            # Prepare files for upload
                            data = aiohttp.FormData()

                            for file_path in saved_files:
                                with open(file_path, 'rb') as f:
                                    data.add_field('files', f, filename=os.path.basename(file_path))

                            data.add_field('config', json.dumps(config))

                            async with session.post(f"{API_BASE_URL}/ingest", data=data) as response:
                                if response.status != 200:
                                    yield f"data: {json.dumps({'type': 'error', 'message': f'Ingestion failed: HTTP {response.status}'})}\n\n"
                                    return

                                # Stream response
                                async for line in response.content:
                                    if line:
                                        yield line.decode('utf-8')

                    # Run async ingestion
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        async for chunk in run_ingestion():
                            yield chunk
                    finally:
                        loop.close()

                except Exception as e:
                    logger.error(f"Ingestion failed: {e}")
                    yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
                finally:
                    # Clean up temporary files
                    shutil.rmtree(temp_dir, ignore_errors=True)

            return Response(
                generate_progress(),
                mimetype='text/event-stream',
                headers={
                    'Cache-Control': 'no-cache',
                    'Connection': 'keep-alive',
                    'Access-Control-Allow-Origin': '*'
                }
            )

        except Exception as e:
            # Clean up on error
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise e

    except Exception as e:
        logger.error(f"Document ingestion failed: {e}")
        return jsonify({"error": "Document ingestion failed"}), 500

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
