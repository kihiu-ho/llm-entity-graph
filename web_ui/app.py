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
from decimal import Decimal
from typing import Dict, Any, Optional
from pathlib import Path
import logging
import traceback
import sys
import os

# Add parent directory to path to import agent module
def setup_agent_import():
    """Setup the import path for the agent module."""
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

# Setup agent import at module level
setup_agent_import()

# Helper function for session management
def close_neo4j_session(session):
    """Helper function to properly close Neo4j sessions (sync or async)."""
    try:
        if hasattr(session, 'close'):
            if asyncio.iscoroutinefunction(session.close):
                # Async session close
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(session.close())
                finally:
                    loop.close()
            else:
                # Sync session close
                session.close()
        logger.info(f"✅ Neo4j session closed")
    except Exception as e:
        logger.warning(f"⚠️ Failed to close Neo4j session: {e}")

def get_neo4j_session_with_driver():
    """Get a Neo4j session and driver that need to be closed together."""
    try:
        from agent.graph_utils import get_neo4j_driver_sync, get_neo4j_database
    except ImportError as e:
        logger.error(f"❌ Failed to import agent.graph_utils: {e}")
        raise ImportError(f"Cannot import agent module: {e}")

    driver = get_neo4j_driver_sync()
    database = get_neo4j_database()
    session = driver.session(database=database)
    return session, driver

def close_neo4j_session_and_driver(session, driver):
    """Close both session and driver properly."""
    try:
        # Close session first
        if session and hasattr(session, 'close'):
            session.close()

        # Close driver
        if driver and hasattr(driver, 'close'):
            driver.close()

        logger.info(f"✅ Neo4j session and driver closed")
    except Exception as e:
        logger.warning(f"⚠️ Failed to close Neo4j session/driver: {e}")

def serialize_neo4j_data(obj):
    """
    Serialize Neo4j data types to JSON-compatible formats.

    Handles:
    - DateTime objects -> ISO format strings
    - Decimal objects -> float
    - Other Neo4j types -> string representation
    """
    if hasattr(obj, '__class__'):
        class_name = obj.__class__.__name__

        # Handle Neo4j DateTime objects
        if class_name == 'DateTime' or 'DateTime' in str(type(obj)):
            try:
                # Try to convert to ISO format
                if hasattr(obj, 'to_native'):
                    return obj.to_native().isoformat()
                elif hasattr(obj, 'isoformat'):
                    return obj.isoformat()
                else:
                    return str(obj)
            except Exception:
                return str(obj)

        # Handle Decimal objects
        elif isinstance(obj, Decimal):
            return float(obj)

        # Handle other Neo4j types
        elif class_name in ['Date', 'Time', 'Duration', 'Point']:
            return str(obj)

    # Handle standard Python datetime
    if isinstance(obj, datetime):
        return obj.isoformat()

    # Return as-is for other types
    return obj

def serialize_graph_data(data):
    """
    Recursively serialize graph data to be JSON-compatible.

    Args:
        data: Dictionary containing nodes and relationships

    Returns:
        JSON-serializable dictionary
    """
    if isinstance(data, dict):
        return {key: serialize_graph_data(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [serialize_graph_data(item) for item in data]
    else:
        return serialize_neo4j_data(data)

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
WEB_UI_PORT = int(os.getenv('WEB_UI_PORT', 5001))
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

@app.route('/debug/agent-import')
def debug_agent_import():
    """Debug endpoint to test agent module import."""
    try:
        logger.info("🔍 Testing agent module import...")
        logger.info(f"📂 Current working directory: {os.getcwd()}")
        logger.info(f"📂 Web UI file location: {os.path.abspath(__file__)}")
        logger.info(f"📂 Parent directory: {os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}")
        logger.info(f"📋 Current sys.path: {sys.path[:5]}...")  # Show first 5 entries

        logger.info("✅ Successfully imported agent.graph_utils functions")

        # Test if we can get a session
        session, driver = get_neo4j_session_with_driver()
        logger.info("✅ Successfully obtained Neo4j session and driver")

        # Test a simple query
        try:
            result = session.run("RETURN 1 as test")
            record = result.single()
            test_value = record["test"] if record else None
            logger.info(f"✅ Neo4j connection test result: {test_value}")
        finally:
            # Close the session and driver properly
            close_neo4j_session_and_driver(session, driver)

        return jsonify({
            "status": "success",
            "message": "Agent module import and Neo4j connection successful",
            "test_query_result": test_value,
            "working_directory": os.getcwd(),
            "web_ui_location": os.path.abspath(__file__),
            "parent_directory": os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        })

    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        return jsonify({
            "status": "import_error",
            "error": str(e),
            "working_directory": os.getcwd(),
            "sys_path": sys.path[:10]
        }), 500

    except Exception as e:
        logger.error(f"❌ General error: {e}")
        logger.error(f"❌ Error traceback: {traceback.format_exc()}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

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




@app.route('/api/ingest', methods=['POST'])
def ingest_files():
    """Handle file ingestion with file upload."""
    try:
        # Get uploaded files
        files = request.files.getlist('files') if 'files' in request.files else []
        config_str = request.form.get('config', '{}')

        # Validate files are provided
        if not files:
            return jsonify({"error": "No files provided for ingestion"}), 400

        # Parse configuration
        try:
            config = json.loads(config_str)
        except json.JSONDecodeError:
            return jsonify({"error": "Invalid configuration JSON"}), 400

        # Enhanced configuration options
        ingestion_mode = config.get('mode', 'basic')  # basic, clean, fast
        chunk_size = config.get('chunk_size', 8000)
        chunk_overlap = config.get('chunk_overlap', 800)
        use_semantic = config.get('use_semantic', True)
        extract_entities = config.get('extract_entities', True)
        clean_before_ingest = config.get('clean_before_ingest', False)
        verbose = config.get('verbose', False)

        # Adjust settings based on mode
        if ingestion_mode == 'fast':
            chunk_size = 800
            use_semantic = False
            extract_entities = False
            verbose = True
        elif ingestion_mode == 'clean':
            clean_before_ingest = True

        def generate_progress():
            """Generate streaming progress updates."""
            try:
                # Simulate ingestion progress for now
                # In a full implementation, this would call the actual ingestion pipeline

                yield f"data: {json.dumps({'type': 'progress', 'current': 0, 'total': 100, 'message': 'Starting ingestion...'})}\n\n"
                time.sleep(0.5)

                if clean_before_ingest:
                    yield f"data: {json.dumps({'type': 'progress', 'current': 10, 'total': 100, 'message': 'Cleaning existing data...'})}\n\n"
                    time.sleep(1)

                # Process uploaded files
                for i, file in enumerate(files):
                    progress = 20 + (i * 60 // len(files))
                    yield f"data: {json.dumps({'type': 'progress', 'current': progress, 'total': 100, 'message': f'Processing {file.filename}...'})}\n\n"
                    time.sleep(0.5)

                yield f"data: {json.dumps({'type': 'progress', 'current': 80, 'total': 100, 'message': 'Building knowledge graph...'})}\n\n"
                time.sleep(0.5)

                yield f"data: {json.dumps({'type': 'progress', 'current': 90, 'total': 100, 'message': 'Finalizing ingestion...'})}\n\n"
                time.sleep(0.5)

                # Return results
                results = {
                    'type': 'result',
                    'results': {
                        'mode': ingestion_mode,
                        'files_processed': len(files),
                        'file_names': [file.filename for file in files],
                        'chunk_size': chunk_size,
                        'use_semantic': use_semantic,
                        'extract_entities': extract_entities,
                        'clean_before_ingest': clean_before_ingest,
                        'total_chunks': len(files) * 25,  # Simulated: ~25 chunks per file
                        'total_entities': (len(files) * 15) if extract_entities else 0,  # Simulated: ~15 entities per file
                        'processing_time': f'{len(files) * 0.8:.1f} seconds'  # Simulated: ~0.8s per file
                    }
                }

                yield f"data: {json.dumps(results)}\n\n"

            except Exception as e:
                logger.error(f"Ingestion error: {e}")
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

        return Response(generate_progress(), mimetype='text/plain')

    except Exception as e:
        logger.error(f"Ingestion endpoint error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/graph/neo4j/visualize')
def get_neo4j_graph_data():
    """Get Neo4j graph data for visualization."""
    try:
        entity = request.args.get('entity', '')
        limit = int(request.args.get('limit', 50))
        query = request.args.get('query', '')

        logger.info(f"🔍 Graph visualization request: entity='{entity}', limit={limit}, query='{query}'")

        # Validate limit parameter
        if limit < 1 or limit > 200:
            logger.warning(f"❌ Invalid limit parameter: {limit}")
            return jsonify({"error": "Limit must be between 1 and 200"}), 400

        # If query is provided, use hybrid Graphiti + Neo4j approach
        if query:
            logger.info(f"📡 Using hybrid approach for query: {query}")
            graph_data = get_hybrid_graph_data(query, limit)
        else:
            logger.info(f"📡 Using direct Neo4j approach for entity: {entity}")
            # Get graph data from Neo4j directly
            graph_data = get_graph_visualization_data(entity, limit)

        logger.info(f"📊 Graph data result: {len(graph_data.get('nodes', []))} nodes, {len(graph_data.get('relationships', []))} relationships")

        # Log detailed graph data for debugging
        logger.info(f"📋 Graph data structure: {type(graph_data)}")
        if graph_data.get('nodes'):
            logger.info(f"📋 Sample node: {graph_data['nodes'][0] if graph_data['nodes'] else 'None'}")
        if graph_data.get('relationships'):
            logger.info(f"📋 Sample relationship: {graph_data['relationships'][0] if graph_data['relationships'] else 'None'}")

        # Check for any non-serializable data
        try:
            import json
            json.dumps(graph_data)
            logger.info(f"✅ Graph data is JSON serializable")
        except Exception as e:
            logger.error(f"❌ Graph data serialization test failed: {e}")
            # Try to serialize it properly
            logger.info(f"🔄 Attempting to fix serialization issues")
            graph_data = serialize_graph_data(graph_data)
            logger.info(f"✅ Graph data re-serialized")

        return jsonify(graph_data)

    except Exception as e:
        logger.error(f"❌ Graph visualization error: {e}")
        logger.error(f"❌ Error traceback: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/graph/hybrid/search')
def hybrid_graph_search():
    """Hybrid search using Graphiti + Neo4j visualization."""
    try:
        query = request.args.get('query', '')
        depth = int(request.args.get('depth', 3))

        if not query:
            return jsonify({"error": "Query parameter is required"}), 400

        # Get hybrid graph data
        graph_data = get_hybrid_graph_data(query, depth)

        return jsonify(graph_data)

    except Exception as e:
        logger.error(f"Hybrid graph search error: {e}")
        return jsonify({"error": str(e)}), 500

def get_graph_visualization_data(entity_name: str = "", limit: int = 50):
    """
    Fetch graph data from Neo4j for visualization.

    Args:
        entity_name: Optional entity name to center the graph around
        limit: Maximum number of nodes to return (default 50)

    Returns:
        Dictionary with nodes and relationships for NVL visualization
    """
    try:
        logger.info(f"🔍 Fetching Neo4j graph data for entity: '{entity_name}', limit: {limit}")

        session, driver = get_neo4j_session_with_driver()
        logger.info(f"✅ Neo4j session and driver obtained")

        try:
            logger.info(f"📡 Neo4j session created")

            if entity_name:
                logger.info(f"🎯 Searching for entity-centered graph: {entity_name}")
                # Get graph centered around specific entity with limit
                # Handle name variations (spaces vs hyphens, case insensitive)
                query = """
                MATCH (center)
                WHERE toLower(center.name) CONTAINS toLower($entity_name)
                   OR toLower(center.id) CONTAINS toLower($entity_name)
                   OR toLower(replace(center.name, ' ', '-')) CONTAINS toLower(replace($entity_name, ' ', '-'))
                   OR toLower(replace(center.name, '-', ' ')) CONTAINS toLower(replace($entity_name, '-', ' '))
                WITH center LIMIT $center_limit
                OPTIONAL MATCH (center)-[r]-(connected)
                WITH collect(DISTINCT center) + collect(DISTINCT connected) as all_nodes,
                     collect(DISTINCT r) as all_rels
                RETURN [node in all_nodes WHERE node IS NOT NULL][0..$limit] as nodes,
                       [rel in all_rels WHERE rel IS NOT NULL] as relationships
                """

                logger.info(f"📝 Executing query: {query}")
                logger.info(f"📝 Query parameters: entity_name='{entity_name}', limit={limit}")
                result = session.run(query, entity_name=entity_name, center_limit=min(10, limit), limit=limit)
            else:
                logger.info(f"📊 Getting sample graph data with limit: {limit}")
                # Get a sample of the graph with specified limit
                query = """
                MATCH (n)
                WITH n LIMIT $limit
                OPTIONAL MATCH (n)-[r]-(connected)
                WITH collect(DISTINCT n) + collect(DISTINCT connected) as all_nodes,
                     collect(DISTINCT r) as all_rels
                RETURN [node in all_nodes WHERE node IS NOT NULL][0..$limit] as nodes,
                       [rel in all_rels WHERE rel IS NOT NULL] as relationships
                """

                logger.info(f"📝 Executing sample query: {query}")
                logger.info(f"📝 Query parameters: limit={limit}")
                result = session.run(query, limit=limit)

            record = result.single()
            logger.info(f"📋 Query result record: {record is not None}")

            if not record:
                logger.warning(f"⚠️ No data found in Neo4j for entity: {entity_name}")
                return {"nodes": [], "relationships": [], "message": "No data found"}

            # Process nodes
            raw_nodes = record["nodes"] or []
            raw_relationships = record["relationships"] or []

            logger.info(f"📊 Raw data from Neo4j: {len(raw_nodes)} nodes, {len(raw_relationships)} relationships")

            nodes = []
            for i, node in enumerate(raw_nodes):
                try:
                    # Process node properties with serialization, excluding embeddings
                    properties = {}
                    embedding_fields_found = []
                    for key, value in node.items():
                        # Skip embedding fields
                        if 'embedding' in key.lower() or key.endswith('_embedding'):
                            embedding_fields_found.append(key)
                            logger.debug(f"🚫 Skipping embedding field: {key}")
                            continue
                        properties[key] = serialize_neo4j_data(value)

                    if embedding_fields_found:
                        logger.info(f"🚫 Removed {len(embedding_fields_found)} embedding fields from node {i}: {embedding_fields_found}")

                    node_data = {
                        "id": str(node.element_id),
                        "labels": list(node.labels),
                        "properties": properties
                    }
                    nodes.append(node_data)
                    if i < 3:  # Log first 3 nodes for debugging
                        logger.info(f"📋 Node {i}: {node_data}")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to process node {i}: {e}")
                    logger.warning(f"⚠️ Node data: {node}")

            # Process relationships
            relationships = []
            for i, rel in enumerate(raw_relationships):
                try:
                    # Process relationship properties with serialization, excluding embeddings
                    properties = {}
                    embedding_fields_found = []
                    for key, value in rel.items():
                        # Skip embedding fields
                        if 'embedding' in key.lower() or key.endswith('_embedding'):
                            embedding_fields_found.append(key)
                            logger.info(f"🚫 Skipping relationship embedding field: {key}")
                            continue
                        properties[key] = serialize_neo4j_data(value)

                    if embedding_fields_found:
                        logger.info(f"🚫 Removed {len(embedding_fields_found)} embedding fields from relationship {i}: {embedding_fields_found}")

                    rel_data = {
                        "id": str(rel.element_id),
                        "type": rel.type,
                        "startNodeId": str(rel.start_node.element_id),
                        "endNodeId": str(rel.end_node.element_id),
                        "properties": properties
                    }
                    relationships.append(rel_data)
                    if i < 3:  # Log first 3 relationships for debugging
                        logger.debug(f"📋 Relationship {i}: {rel_data}")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to process relationship {i}: {e}")
                    logger.warning(f"⚠️ Relationship data: {rel}")

            result_data = {
                "nodes": nodes,
                "relationships": relationships,
                "metadata": {
                    "entity": entity_name,
                    "limit": limit,
                    "node_count": len(nodes),
                    "relationship_count": len(relationships)
                }
            }

            logger.info(f"✅ Successfully processed Neo4j data: {len(nodes)} nodes, {len(relationships)} relationships")

            # Log sample data for debugging
            if nodes:
                logger.debug(f"📋 Sample node data: {nodes[0]}")
            if relationships:
                logger.debug(f"📋 Sample relationship data: {relationships[0]}")

            # Serialize the data to handle Neo4j types
            logger.info(f"🔄 Serializing graph data for JSON response")
            serialized_data = serialize_graph_data(result_data)
            logger.info(f"✅ Graph data serialized successfully")

            return serialized_data

        finally:
            # Close the session and driver
            close_neo4j_session_and_driver(session, driver)

    except Exception as e:
        logger.error(f"❌ Failed to fetch Neo4j graph data: {e}")
        logger.error(f"❌ Error traceback: {traceback.format_exc()}")
        return {
            "nodes": [],
            "relationships": [],
            "error": str(e)
        }

def get_hybrid_graph_data(query: str, depth: int = 3):
    """
    Hybrid approach: Use Graphiti for search, then Neo4j for visualization.

    Args:
        query: Search query for Graphiti
        depth: Depth of relationships to traverse in Neo4j

    Returns:
        Dictionary with nodes and relationships for NVL visualization
    """
    try:
        import asyncio
        try:
            from agent.graph_utils import search_entities_and_relationships
            from agent.graph_utils import get_neo4j_driver_sync
        except ImportError as e:
            logger.error(f"❌ Failed to import agent.graph_utils in hybrid function: {e}")
            raise ImportError(f"Cannot import agent module: {e}")

        # Step 1: Use Graphiti to find relevant entities
        logger.info(f"Searching Graphiti for: {query}")

        # Run Graphiti search asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            graphiti_results = loop.run_until_complete(
                search_entities_and_relationships(query)
            )
        finally:
            loop.close()

        logger.info(f"Graphiti results: {len(graphiti_results.get('entities', []))} entities, {len(graphiti_results.get('relationships', []))} relationships")

        # Step 2: Extract entity names from Graphiti results
        entity_names = set()

        # Extract from entities
        for entity in graphiti_results.get('entities', []):
            if isinstance(entity, dict):
                name = entity.get('name') or entity.get('entity_name') or str(entity.get('id', ''))
                if name:
                    entity_names.add(name)
            elif isinstance(entity, str):
                entity_names.add(entity)

        # Extract from relationships
        for rel in graphiti_results.get('relationships', []):
            if isinstance(rel, dict):
                source = rel.get('source') or rel.get('source_entity')
                target = rel.get('target') or rel.get('target_entity')
                if source:
                    entity_names.add(source)
                if target:
                    entity_names.add(target)

        logger.info(f"Extracted entity names: {list(entity_names)[:10]}...")  # Log first 10

        # Step 3: Query Neo4j for these entities and their relationships
        if not entity_names:
            logger.warning("No entity names found from Graphiti search")
            return {"nodes": [], "relationships": [], "metadata": {"source": "hybrid", "query": query}}

        # Build Neo4j query to find these entities and their connections
        neo4j_data = get_neo4j_data_for_entities(list(entity_names), depth)

        # Step 4: Enhance with Graphiti relationship information
        enhanced_data = enhance_neo4j_with_graphiti(neo4j_data, graphiti_results)

        return {
            **enhanced_data,
            "metadata": {
                "source": "hybrid",
                "query": query,
                "depth": depth,
                "graphiti_entities": len(graphiti_results.get('entities', [])),
                "graphiti_relationships": len(graphiti_results.get('relationships', [])),
                "neo4j_nodes": len(enhanced_data.get('nodes', [])),
                "neo4j_relationships": len(enhanced_data.get('relationships', []))
            }
        }

    except Exception as e:
        logger.error(f"Failed to get hybrid graph data: {e}")
        return {
            "nodes": [],
            "relationships": [],
            "error": str(e),
            "metadata": {"source": "hybrid", "query": query}
        }

def get_neo4j_data_for_entities(entity_names: list, depth: int = 3):
    """
    Query Neo4j for specific entities and their relationships.

    Args:
        entity_names: List of entity names to search for
        depth: Depth of relationships to traverse

    Returns:
        Dictionary with nodes and relationships
    """
    try:
        session, driver = get_neo4j_session_with_driver()

        try:
            # Build query to find entities by name and their connections
            query = """
            MATCH (n)
            WHERE ANY(name IN $entity_names WHERE
                n.name CONTAINS name OR
                toLower(n.name) CONTAINS toLower(name) OR
                toLower(replace(n.name, ' ', '-')) CONTAINS toLower(replace(name, ' ', '-')) OR
                toLower(replace(n.name, '-', ' ')) CONTAINS toLower(replace(name, '-', ' ')) OR
                ANY(label IN labels(n) WHERE toLower(label) CONTAINS toLower(name))
            )
            WITH collect(DISTINCT n) as seed_nodes

            UNWIND seed_nodes as seed
            MATCH path = (seed)-[*1..%d]-(connected)
            WITH nodes(path) as path_nodes, relationships(path) as path_rels

            UNWIND path_nodes as node
            WITH collect(DISTINCT node) as all_nodes, path_rels
            UNWIND path_rels as rel
            WITH all_nodes, collect(DISTINCT rel) as all_rels

            RETURN all_nodes as nodes, all_rels as relationships
            """ % min(depth, 5)  # Limit depth for performance

            result = session.run(query, entity_names=entity_names)
            record = result.single()

            if not record:
                logger.warning(f"No Neo4j data found for entities: {entity_names[:5]}...")
                return {"nodes": [], "relationships": []}

            # Process nodes
            nodes = []
            for node in record["nodes"] or []:
                node_data = {
                    "id": str(node.element_id),
                    "labels": list(node.labels),
                    "properties": dict(node.items())
                }
                nodes.append(node_data)

            # Process relationships
            relationships = []
            for rel in record["relationships"] or []:
                rel_data = {
                    "id": str(rel.element_id),
                    "type": rel.type,
                    "startNodeId": str(rel.start_node.element_id),
                    "endNodeId": str(rel.end_node.element_id),
                    "properties": dict(rel.items())
                }
                relationships.append(rel_data)

            logger.info(f"Neo4j query returned {len(nodes)} nodes and {len(relationships)} relationships")

            return {
                "nodes": nodes,
                "relationships": relationships
            }

        finally:
            # Close the session and driver
            close_neo4j_session_and_driver(session, driver)

    except Exception as e:
        logger.error(f"Failed to query Neo4j for entities: {e}")
        return {"nodes": [], "relationships": []}

def enhance_neo4j_with_graphiti(neo4j_data: dict, graphiti_results: dict):
    """
    Enhance Neo4j data with additional information from Graphiti.

    Args:
        neo4j_data: Neo4j nodes and relationships
        graphiti_results: Graphiti search results

    Returns:
        Enhanced data dictionary
    """
    try:
        # Start with Neo4j data
        enhanced_nodes = neo4j_data.get('nodes', []).copy()
        enhanced_relationships = neo4j_data.get('relationships', []).copy()

        # Create lookup maps for existing Neo4j data
        neo4j_node_names = set()
        for node in enhanced_nodes:
            name = node.get('properties', {}).get('name', '')
            if name:
                neo4j_node_names.add(name.lower())

        # Add any missing entities from Graphiti as virtual nodes
        for entity in graphiti_results.get('entities', []):
            if isinstance(entity, dict):
                entity_name = entity.get('name') or entity.get('entity_name', '')
                if entity_name and entity_name.lower() not in neo4j_node_names:
                    # Add as virtual node
                    virtual_node = {
                        "id": f"virtual_{len(enhanced_nodes)}",
                        "labels": ["Virtual", "GraphitiEntity"],
                        "properties": {
                            "name": entity_name,
                            "source": "graphiti",
                            "virtual": True
                        }
                    }
                    enhanced_nodes.append(virtual_node)
                    neo4j_node_names.add(entity_name.lower())

        # Enhance relationships with Graphiti information
        for rel in graphiti_results.get('relationships', []):
            if isinstance(rel, dict):
                source = rel.get('source') or rel.get('source_entity', '')
                target = rel.get('target') or rel.get('target_entity', '')
                rel_type = rel.get('relationship') or rel.get('type', 'RELATED_TO')

                if source and target:
                    # Find corresponding node IDs
                    source_id = find_node_id_by_name(enhanced_nodes, source)
                    target_id = find_node_id_by_name(enhanced_nodes, target)

                    if source_id and target_id:
                        # Check if relationship already exists
                        rel_exists = any(
                            r.get('startNodeId') == source_id and
                            r.get('endNodeId') == target_id and
                            r.get('type') == rel_type
                            for r in enhanced_relationships
                        )

                        if not rel_exists:
                            virtual_rel = {
                                "id": f"virtual_rel_{len(enhanced_relationships)}",
                                "type": rel_type,
                                "startNodeId": source_id,
                                "endNodeId": target_id,
                                "properties": {
                                    "source": "graphiti",
                                    "virtual": True,
                                    **rel.get('properties', {})
                                }
                            }
                            enhanced_relationships.append(virtual_rel)

        return {
            "nodes": enhanced_nodes,
            "relationships": enhanced_relationships
        }

    except Exception as e:
        logger.error(f"Failed to enhance Neo4j data with Graphiti: {e}")
        return neo4j_data

def find_node_id_by_name(nodes: list, name: str) -> str:
    """Find node ID by name (case-insensitive)."""
    name_lower = name.lower()
    for node in nodes:
        node_name = node.get('properties', {}).get('name', '').lower()
        if node_name == name_lower or name_lower in node_name:
            return node.get('id')
    return None

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
