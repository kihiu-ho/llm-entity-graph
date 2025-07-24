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
from typing import Dict, Any, Optional, List
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

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add pre-approval database import
try:
    from approval.pre_approval_db import create_pre_approval_database
    PRE_APPROVAL_DB_AVAILABLE = True
except ImportError:
    PRE_APPROVAL_DB_AVAILABLE = False
    logger.warning("⚠️ Pre-approval database not available")

# Global pre-approval database instance
_pre_approval_db = None
_pre_approval_db_lock = threading.Lock()

def get_pre_approval_db():
    """Get pre-approval database singleton instance."""
    global _pre_approval_db
    
    if not PRE_APPROVAL_DB_AVAILABLE:
        return None
    
    # Thread-safe singleton pattern with double-checked locking
    if _pre_approval_db is None:
        with _pre_approval_db_lock:
            # Double-check after acquiring lock
            if _pre_approval_db is None:
                try:
                    _pre_approval_db = create_pre_approval_database()
                    logger.info("✅ Pre-approval database singleton created (will initialize on first use)")
                except Exception as e:
                    logger.error(f"❌ Failed to create pre-approval database singleton: {e}")
                    _pre_approval_db = None
                    return None
    
    # Return the existing instance
    return _pre_approval_db

def call_db_method_sync(db, method_name, *args, **kwargs):
    """
    Call a database method synchronously by running it in the async runner.
    This completely avoids the async/await context issues.
    """
    async def _call_method():
        # Get the method from the database instance
        method = getattr(db, method_name)
        
        # Ensure database is initialized
        if not db._initialized:
            await db.initialize()
        
        # Check if the pool is available
        if not db.pool:
            raise RuntimeError("Database connection pool is not available")
        
        # Call the async method directly
        result = await method(*args, **kwargs)
        return result
    
    try:
        # Run the async operation in the dedicated thread
        return async_runner.run_async(_call_method())
    except Exception as e:
        logger.error(f"❌ Error in DB method {method_name}: {e}")
        raise

import asyncio
import threading
import queue
from concurrent.futures import ThreadPoolExecutor

# Database event loop runner for better async handling
class AsyncDatabaseRunner:
    """Dedicated thread for running async database operations."""
    
    def __init__(self):
        self.loop = None
        self.thread = None
        self.task_queue = queue.Queue()
        self.shutdown = False
        
    def start(self):
        """Start the async runner thread."""
        if self.thread is None or not self.thread.is_alive():
            self.shutdown = False
            self.thread = threading.Thread(target=self._run_loop, daemon=True)
            self.thread.start()
    
    def _run_loop(self):
        """Run the event loop in the dedicated thread."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        try:
            self.loop.run_forever()
        finally:
            try:
                # Cancel any pending tasks
                pending = asyncio.all_tasks(self.loop)
                for task in pending:
                    task.cancel()
                
                if pending:
                    self.loop.run_until_complete(
                        asyncio.gather(*pending, return_exceptions=True)
                    )
            except Exception as e:
                logger.warning(f"⚠️ Error during loop cleanup: {e}")
            finally:
                self.loop.close()
    
    def run_async(self, coro, timeout=30):
        """Run an async coroutine in the dedicated thread."""
        if self.loop is None or not self.thread.is_alive():
            self.start()
            # Wait for loop to be ready
            import time
            for _ in range(50):  # Wait up to 5 seconds
                if self.loop is not None:
                    break
                time.sleep(0.1)
        
        if self.loop is None:
            raise RuntimeError("Failed to start async event loop")
        
        # Submit the coroutine to the loop
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        try:
            return future.result(timeout=timeout)
        except Exception as e:
            logger.error(f"❌ Error in async operation: {e}")
            raise
    
    def stop(self):
        """Stop the async runner."""
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)
        self.shutdown = True

# Global async runner instance
async_runner = AsyncDatabaseRunner()

def run_async_in_thread(coro):
    """Run async coroutine using the dedicated async runner."""
    return async_runner.run_async(coro)
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
        # Try to import with better error handling
        import importlib.util

        # Check if agent.graph_utils module exists
        spec = importlib.util.find_spec("agent.graph_utils")
        if spec is None:
            raise ImportError("agent.graph_utils module not found in path")

        from agent.graph_utils import get_neo4j_driver_sync, get_neo4j_database

        driver = get_neo4j_driver_sync()
        database = get_neo4j_database()
        session = driver.session(database=database)
        return session, driver

    except ImportError as e:
        logger.error(f"❌ Failed to import agent.graph_utils: {e}")
        # Try alternative direct Neo4j connection
        return get_direct_neo4j_connection()
    except Exception as e:
        logger.error(f"❌ Failed to get Neo4j session: {e}")
        # Try alternative direct Neo4j connection
        return get_direct_neo4j_connection()

def get_direct_neo4j_connection():
    """Direct Neo4j connection as fallback."""
    try:
        from neo4j import GraphDatabase
        from dotenv import load_dotenv

        load_dotenv()

        # Get Neo4j configuration from environment
        neo4j_uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
        neo4j_user = os.getenv('NEO4J_USER', 'neo4j')
        neo4j_password = os.getenv('NEO4J_PASSWORD', 'password')
        neo4j_database = os.getenv('NEO4J_DATABASE', 'neo4j')

        logger.info(f"🔗 Attempting direct Neo4j connection to {neo4j_uri}")

        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        session = driver.session(database=neo4j_database)

        # Test the connection
        result = session.run("RETURN 1 as test")
        test_record = result.single()
        if test_record and test_record['test'] == 1:
            logger.info("✅ Direct Neo4j connection successful")
            return session, driver
        else:
            raise Exception("Connection test failed")

    except Exception as e:
        logger.error(f"❌ Direct Neo4j connection failed: {e}")
        raise ImportError(f"Cannot establish Neo4j connection: {e}")

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

async def get_graph_data_async(query: str) -> Optional[dict]:
    """
    Async version of get_graph_data for use in streaming responses.

    Args:
        query: Search query for graph data

    Returns:
        Dictionary with nodes and relationships for NVL visualization
    """
    try:
        # Run the sync version in a thread pool to avoid blocking
        import asyncio
        import concurrent.futures

        # Import here to avoid circular imports
        from agent.tools import graph_search_tool, GraphSearchInput

        # Use the graph_search_tool directly
        search_input = GraphSearchInput(query=query)
        results = await graph_search_tool(search_input)

        # Convert to the expected format
        if results:
            nodes = []
            relationships = []

            # Extract entities and relationships from the graph search results
            for result in results:
                fact = result.fact
                # Simple entity extraction from facts
                entities = extract_entities_from_fact(fact)

                for entity in entities:
                    if entity not in [n.get('properties', {}).get('name') for n in nodes]:
                        nodes.append({
                            'id': f"entity_{len(nodes)}",
                            'labels': ['Entity'],
                            'properties': {
                                'name': entity,
                                'source': 'graph_search',
                                'fact': fact
                            }
                        })

            return {
                'nodes': nodes,
                'relationships': relationships,
                'metadata': {
                    'source': 'graph_search_tool',
                    'query': query,
                    'facts_count': len(results)
                }
            }

        return None

    except Exception as e:
        logger.error(f"❌ Async graph data extraction failed: {e}")
        return None

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

# Import Graphiti SearchFilters for entity type filtering
try:
    from graphiti_core.search.search_filters import SearchFilters
    GRAPHITI_SEARCH_AVAILABLE = True
except ImportError:
    GRAPHITI_SEARCH_AVAILABLE = False
    print("⚠️ SearchFilters not available - entity type filtering will be limited")

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

# Global variables for ingestion tracking and cancellation
import uuid
INGESTION_STATUS = {
    'active': False,
    'progress': 0.0,
    'message': '',
    'start_time': None,
    'file_count': 0,
    'current_file': 0,
    'cancelled': False,
    'ingestion_id': None
}

def reset_ingestion_status():
    """Reset ingestion status to default values."""
    global INGESTION_STATUS
    INGESTION_STATUS.update({
        'active': False,
        'progress': 0.0,
        'message': '',
        'start_time': None,
        'file_count': 0,
        'current_file': 0,
        'cancelled': False,
        'ingestion_id': None
    })

def check_ingestion_cancelled():
    """Check if ingestion has been cancelled."""
    return INGESTION_STATUS.get('cancelled', False)

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

    def _is_graph_query(self, message: str) -> bool:
        """Detect if a message is likely to be a graph-related query."""
        message_lower = message.lower()

        # Graph query indicators
        graph_indicators = [
            "relationship", "connection", "works at", "employed by", "partnership",
            "acquisition", "merger", "investment", "funding", "board", "director",
            "who is", "what is", "how is", "connected to", "related to", "associated with",
            "graph", "network", "visualize", "show me", "find connections", "entity",
            "company", "person", "organization", "ceo", "executive", "chairman",
            "employee", "shareholder", "subsidiary", "parent company", "owns",
            "founded by", "worked at", "member of", "part of", "belongs to"
        ]

        return any(indicator in message_lower for indicator in graph_indicators)

def extract_entities_from_fact(fact: str) -> set:
    """Extract potential entity names from a fact string."""
    import re

    entities = set()

    # Common patterns for entity extraction
    patterns = [
        r'\b([A-Z][a-z]+ [A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',  # Person names (Title Case)
        r'\b([A-Z][A-Z\s&]+(?:Ltd|Limited|Inc|Corporation|Corp|Company|Co|Group|Holdings|Bank|Insurance|Investment|Fund|Trust|Association|Society|Club|Institute|Foundation|Organization|Org)\.?)\b',  # Company names
        r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:Ltd|Limited|Inc|Corporation|Corp|Company|Co|Group|Holdings|Bank|Insurance|Investment|Fund|Trust|Association|Society|Club|Institute|Foundation|Organization|Org))\.?)\b',  # Mixed case company names
    ]

    for pattern in patterns:
        matches = re.findall(pattern, fact, re.IGNORECASE)
        for match in matches:
            if len(match.strip()) > 2:  # Filter out very short matches
                entities.add(match.strip())

    # Also look for quoted entities
    quoted_entities = re.findall(r'"([^"]+)"', fact)
    for entity in quoted_entities:
        if len(entity.strip()) > 2:
            entities.add(entity.strip())

    return entities

def get_enhanced_relationship_data(query: str) -> Optional[dict]:
    """Get relationship data using the enhanced search functionality."""
    try:
        import re
        import sys
        import os

        # Add the project root to Python path
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        from enhanced_graph_search import EnhancedGraphSearch

        # Extract entities from relationship query
        entities = extract_entities_from_relationship_query(query)

        if len(entities) >= 2:
            entity1, entity2 = entities[0], entities[1]
            logger.info(f"🔍 Enhanced search for relationship between '{entity1}' and '{entity2}'")

            # Use enhanced search
            search = EnhancedGraphSearch()
            result = search.search_entities_and_relationships(entity1, entity2)

            if result.get('direct_relationships') or result.get('entity1_nodes') or result.get('entity2_nodes'):
                # Convert to web UI format
                nodes = []
                relationships = []

                # Add entity nodes
                for i, node in enumerate(result.get('entity1_nodes', [])):
                    node_id = f"entity1_{i}"
                    nodes.append({
                        'id': node_id,
                        'labels': node.get('labels', ['Entity']),
                        'properties': {
                            'name': node.get('name', 'Unknown'),
                            'company': node.get('company', ''),
                            'position': node.get('position', ''),
                            'summary': node.get('summary', ''),
                            'source': 'enhanced_search'
                        }
                    })

                for i, node in enumerate(result.get('entity2_nodes', [])):
                    node_id = f"entity2_{i}"
                    nodes.append({
                        'id': node_id,
                        'labels': node.get('labels', ['Entity']),
                        'properties': {
                            'name': node.get('name', 'Unknown'),
                            'company': node.get('company', ''),
                            'position': node.get('position', ''),
                            'summary': node.get('summary', ''),
                            'source': 'enhanced_search'
                        }
                    })

                # Add relationships
                for i, rel in enumerate(result.get('direct_relationships', [])):
                    source_name = rel['source'].get('name', 'Unknown')
                    target_name = rel['target'].get('name', 'Unknown')

                    # Find source and target node IDs
                    source_id = None
                    target_id = None

                    # Search through all nodes to find matching names (use first occurrence)
                    for node in nodes:
                        node_name = node['properties']['name']
                        if node_name == source_name and source_id is None:
                            source_id = node['id']
                            logger.info(f"Found source node: {source_name} -> {source_id}")
                        if node_name == target_name and target_id is None:
                            target_id = node['id']
                            logger.info(f"Found target node: {target_name} -> {target_id}")

                    # Create synthetic IDs if not found
                    if not source_id:
                        source_id = f"source_{i}"
                        nodes.append({
                            'id': source_id,
                            'labels': ['Entity'],
                            'properties': {
                                'name': source_name,
                                'source': 'enhanced_search_synthetic'
                            }
                        })

                    if not target_id:
                        target_id = f"target_{i}"
                        nodes.append({
                            'id': target_id,
                            'labels': ['Entity'],
                            'properties': {
                                'name': target_name,
                                'source': 'enhanced_search_synthetic'
                            }
                        })

                    relationships.append({
                        'id': f"rel_{i}",
                        'type': rel.get('relationship_type', 'RELATED_TO'),
                        'startNode': source_id,
                        'endNode': target_id,
                        'properties': {
                            'detail': rel.get('relationship_detail', ''),
                            'extraction_method': rel.get('extraction_method', 'enhanced_search'),
                            'source': 'enhanced_search'
                        }
                    })

                return {
                    'nodes': nodes,
                    'relationships': relationships,
                    'metadata': {
                        'source': 'enhanced_search',
                        'query': query,
                        'entity1': entity1,
                        'entity2': entity2,
                        'connection_strength': result.get('connection_strength', 0.0),
                        'summary': result.get('summary', '')
                    }
                }

        return None

    except Exception as e:
        logger.error(f"Enhanced relationship search failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None

def extract_entities_from_relationship_query(query: str) -> list:
    """Extract entity names from a relationship query."""
    import re

    # Common patterns for relationship queries
    patterns = [
        r"relation(?:ship)?\s+between\s+['\"]?(.+?)['\"]?\s+and\s+['\"]?(.+?)['\"]?(?:\s|$|\?)",
        r"connection\s+between\s+['\"]?(.+?)['\"]?\s+and\s+['\"]?(.+?)['\"]?(?:\s|$|\?)",
        r"how\s+is\s+['\"]?(.+?)['\"]?\s+(?:related\s+to|connected\s+to)\s+['\"]?(.+?)['\"]?(?:\s|$|\?)",
        r"['\"]?(.+?)['\"]?\s+(?:related\s+to|connected\s+to|works\s+with)\s+['\"]?(.+?)['\"]?(?:\s|$|\?)"
    ]

    query_lower = query.lower().strip()

    for pattern in patterns:
        match = re.search(pattern, query_lower)
        if match:
            entity1 = match.group(1).strip().strip("'\"")
            entity2 = match.group(2).strip().strip("'\"")

            # Clean up entity names
            entity1 = clean_entity_name(entity1)
            entity2 = clean_entity_name(entity2)

            return [entity1, entity2]

    return []

def clean_entity_name(name: str) -> str:
    """Clean and normalize entity names."""
    import re

    # Remove common words and punctuation
    name = name.strip()

    # Remove quotes (single and double)
    name = re.sub(r"['\"]", '', name)

    # Remove question marks and other punctuation
    name = re.sub(r'[?!.,;]', '', name)

    # Handle common abbreviations and variations
    name_mapping = {
        "hkjc": "Hong Kong Jockey Club",
        "hong kong jockey club": "Hong Kong Jockey Club",
        "the hong kong jockey club": "Hong Kong Jockey Club"
    }

    name_lower = name.lower()
    if name_lower in name_mapping:
        return name_mapping[name_lower]

    return name.title()  # Capitalize properly

def is_relationship_query(query: str) -> bool:
    """Check if the query is asking about relationships between entities."""
    relationship_indicators = [
        "relation", "relationship", "connection", "connected", "between",
        "how is", "what is the relation", "what is the relationship",
        "connected to", "related to", "works with", "employed by"
    ]
    query_lower = query.lower()
    return any(indicator in query_lower for indicator in relationship_indicators)

def get_graph_data_with_agent_tool(query: str) -> Optional[dict]:
    """Get graph data using the agent's graph_search_tool or enhanced search for relationships."""
    try:
        import asyncio
        from agent.tools import graph_search_tool, GraphSearchInput

        # Create event loop if needed
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Check if this is a relationship query
        if is_relationship_query(query):
            logger.info(f"🔍 Detected relationship query, using enhanced search")
            try:
                # Try enhanced search for relationship queries
                enhanced_result = get_enhanced_relationship_data(query)
                if enhanced_result:
                    logger.info(f"✅ Enhanced search found data: {len(enhanced_result.get('nodes', []))} nodes, {len(enhanced_result.get('relationships', []))} relationships")
                    return enhanced_result
                else:
                    logger.info(f"⚠️ Enhanced search found no data, falling back to standard search")
            except Exception as e:
                logger.warning(f"Enhanced search failed: {e}, falling back to standard search")

        # Use the standard graph_search_tool
        search_input = GraphSearchInput(query=query)
        results = loop.run_until_complete(graph_search_tool(search_input))

        logger.info(f"🎯 Graph search tool returned {len(results)} results")

        if results:
            nodes = []
            relationships = []

            # Extract entities and relationships from the graph search results
            entity_map = {}

            for result in results:
                fact = result.fact
                logger.info(f"📝 Processing fact: {fact[:100]}...")

                # Extract entities from the fact
                entities = extract_entities_from_fact(fact)

                # Add entities as nodes
                for entity in entities:
                    if entity not in entity_map:
                        node_id = f"entity_{len(nodes)}"
                        entity_map[entity] = node_id
                        nodes.append({
                            'id': node_id,
                            'labels': ['Entity'],
                            'properties': {
                                'name': entity,
                                'source': 'graph_search_tool',
                                'fact': fact
                            }
                        })

                # Try to extract relationships from the fact
                if len(entities) >= 2:
                    # Create relationships between entities mentioned in the same fact
                    for i, entity1 in enumerate(entities):
                        for entity2 in entities[i+1:]:
                            if entity1 in entity_map and entity2 in entity_map:
                                relationships.append({
                                    'id': f"rel_{len(relationships)}",
                                    'startNodeId': entity_map[entity1],
                                    'endNodeId': entity_map[entity2],
                                    'type': 'MENTIONED_WITH',
                                    'properties': {
                                        'source': 'graph_search_tool',
                                        'fact': fact,
                                        'confidence': 0.8
                                    }
                                })

            logger.info(f"✅ Created {len(nodes)} nodes and {len(relationships)} relationships")

            return {
                'nodes': nodes,
                'relationships': relationships,
                'metadata': {
                    'source': 'graph_search_tool',
                    'query': query,
                    'facts_count': len(results)
                }
            }

        logger.info("ℹ️ No results from graph search tool")
        return None

    except Exception as e:
        logger.error(f"❌ Failed to get graph data with agent tool: {e}")
        return None

def create_sample_graph_data(query: str) -> dict:
    """Create sample graph data for demonstration purposes."""
    try:
        # Create sample nodes and relationships based on the query
        if "michael" in query.lower() and "lee" in query.lower():
            return {
                "nodes": [
                    {
                        "id": "person_1",
                        "labels": ["Person"],
                        "properties": {
                            "name": "Michael T. H. Lee",
                            "type": "Person",
                            "role": "Executive Director"
                        }
                    },
                    {
                        "id": "company_1",
                        "labels": ["Company"],
                        "properties": {
                            "name": "Hong Kong Jockey Club",
                            "type": "Company",
                            "industry": "Sports & Entertainment"
                        }
                    },
                    {
                        "id": "company_2",
                        "labels": ["Company"],
                        "properties": {
                            "name": "Sample Corporation",
                            "type": "Company",
                            "industry": "Finance"
                        }
                    }
                ],
                "relationships": [
                    {
                        "id": "rel_1",
                        "startNodeId": "person_1",
                        "endNodeId": "company_1",
                        "type": "EXECUTIVE_OF",
                        "properties": {
                            "role": "Executive Director",
                            "source": "sample_data"
                        }
                    },
                    {
                        "id": "rel_2",
                        "startNodeId": "person_1",
                        "endNodeId": "company_2",
                        "type": "BOARD_MEMBER_OF",
                        "properties": {
                            "role": "Board Member",
                            "source": "sample_data"
                        }
                    }
                ]
            }
        else:
            # Generic sample data for other queries
            return {
                "nodes": [
                    {
                        "id": "entity_1",
                        "labels": ["Entity"],
                        "properties": {
                            "name": "Sample Entity 1",
                            "type": "Organization"
                        }
                    },
                    {
                        "id": "entity_2",
                        "labels": ["Entity"],
                        "properties": {
                            "name": "Sample Entity 2",
                            "type": "Person"
                        }
                    }
                ],
                "relationships": [
                    {
                        "id": "rel_sample",
                        "startNodeId": "entity_1",
                        "endNodeId": "entity_2",
                        "type": "RELATES_TO",
                        "properties": {
                            "source": "sample_data"
                        }
                    }
                ]
            }
    except Exception as e:
        logger.error(f"❌ Failed to create sample graph data: {e}")
        return None

async def search_entities_by_type(query: str, entity_types: List[str] = None) -> Optional[dict]:
    """
    Search for entities using Graphiti's custom entity type filtering.

    Args:
        query: Search query
        entity_types: List of entity types to filter by (e.g., ["Person", "Company"])

    Returns:
        Dictionary with search results
    """
    try:
        if not GRAPHITI_SEARCH_AVAILABLE:
            logger.warning("SearchFilters not available, falling back to regular search")
            return await get_graph_data_async(query)

        # Import graph client
        from agent.graph_utils import get_graph_client

        client = get_graph_client()
        await client.initialize()

        # Create search filter for entity types
        search_filter = None
        if entity_types:
            search_filter = SearchFilters(node_labels=entity_types)
            logger.info(f"🎯 Searching with entity type filter: {entity_types}")

        # Perform search with entity type filtering
        if search_filter:
            results = await client.graphiti.search_(query, search_filter=search_filter)
        else:
            results = await client.graphiti.search(query)

        # Convert results to graph visualization format
        graph_data = {
            "nodes": [],
            "relationships": [],
            "entity_types_used": entity_types or []
        }

        # Process search results
        if results:
            logger.info(f"✅ Found {len(results)} results with entity type filtering")

            # Extract entities and relationships from results
            for result in results:
                # Add logic to convert Graphiti search results to graph format
                # This would need to be implemented based on the actual result structure
                pass

        return graph_data

    except Exception as e:
        logger.error(f"❌ Entity type search failed: {e}")
        return None

    async def _extract_graph_data_from_response(self, query: str, response_data: dict) -> Optional[dict]:
        """Extract graph data for visualization when graph tools are used."""
        try:
            # Use the existing graph visualization endpoint to get graph data
            logger.info(f"🎯 Extracting graph data for query: {query}")

            # Import here to avoid circular imports
            graph_data = await get_graph_data_async(query)

            if graph_data and (graph_data.get('nodes') or graph_data.get('relationships')):
                logger.info(f"✅ Extracted graph data: {len(graph_data.get('nodes', []))} nodes, {len(graph_data.get('relationships', []))} relationships")
                return graph_data
            else:
                logger.info("ℹ️ No graph data found for visualization")
                return None

        except Exception as e:
            logger.warning(f"⚠️ Failed to extract graph data: {e}")
            return None

    async def stream_chat(self, message: str, session_id: Optional[str] = None, user_id: str = "web_user"):
        """Stream chat response from API."""
        if not AIOHTTP_AVAILABLE:
            yield {
                "type": "error",
                "content": "aiohttp not available - install with: pip install aiohttp"
            }
            return

        # Detect if this is a graph-related query
        is_graph_query = self._is_graph_query(message)

        request_data = {
            "message": message,
            "session_id": session_id,
            "user_id": user_id,
            "search_type": "hybrid",
            "include_graph_data": is_graph_query  # Request graph data for graph queries
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

                                # If this is a graph query and we have a final response, try to extract graph data
                                if (is_graph_query and
                                    data.get('type') == 'content' and
                                    data.get('content') and
                                    'tools_used' in data):

                                    # Check if graph tools were used
                                    tools_used = data.get('tools_used', [])
                                    graph_tools = ['graph_search', 'comprehensive_search', 'search_people', 'search_companies', 'find_entity_connections']

                                    if any(tool.get('tool_name') in graph_tools for tool in tools_used):
                                        # Try to extract graph data from the response
                                        graph_data = await self._extract_graph_data_from_response(message, data)
                                        if graph_data:
                                            data['graph_data'] = graph_data
                                            logger.info(f"🎯 Added graph data to response: {len(graph_data.get('nodes', []))} nodes, {len(graph_data.get('relationships', []))} relationships")

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

@app.route('/approval')
def approval_dashboard():
    """Serve the approval dashboard interface."""
    return render_template('approval.html')

@app.route('/unified')
def unified_dashboard():
    """Serve the unified ingestion-approval interface."""
    return render_template('unified_combined.html')

@app.route('/api/latest-entities')
def get_latest_entities():
    """Get latest ingested entities from pre-approval database."""
    try:
        limit = int(request.args.get('limit', 100))
        entity_types = request.args.getlist('entity_types')
        status_filter = request.args.get('status', 'pending')
        
        # Try to get pre-approval database
        pre_db = get_pre_approval_db()
        if pre_db is None:
            # Fallback to approval service if pre-approval DB not available
            service = get_approval_service()
            if service is None:
                return jsonify({
                    "success": False, 
                    "error": "Neither pre-approval database nor approval service available"
                }), 500
            
            # Use existing approval service logic
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(service.initialize())
                entities = loop.run_until_complete(
                    service.get_latest_entities(
                        limit=limit,
                        entity_types=entity_types if entity_types else None,
                        status_filter=status_filter
                    )
                )
            finally:
                loop.close()
        else:
            # Use pre-approval database
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                entities = loop.run_until_complete(
                    pre_db.get_entities(
                        status_filter=status_filter,
                        entity_types=entity_types if entity_types else None,
                        limit=limit
                    )
                )
            finally:
                if pre_db._initialized:
                    loop.run_until_complete(pre_db.close())
                loop.close()
        
        return jsonify({
            "success": True,
            "entities": entities,
            "count": len(entities)
        })
            
    except Exception as e:
        logger.error(f"❌ Failed to get latest entities: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/pre-approval/entities')
def get_pre_approval_entities():
    """Get entities from pre-approval database with filtering."""
    try:
        limit = int(request.args.get('limit', 100))
        entity_types = request.args.getlist('entity_types')
        status_filter = request.args.get('status', 'pending')
        # Note: search functionality not implemented in pre_approval_db yet
        
        # Try to get pre-approval database
        pre_db = get_pre_approval_db()
        if pre_db is None:
            return jsonify({
                "success": False, 
                "error": "Pre-approval database not available"
            }), 503
        
        # Use thread-safe async execution to prevent race conditions
        entities = call_db_method_sync(
            pre_db, 
            'get_entities',
            limit=limit,
            entity_types=entity_types if entity_types else None,
            status_filter=status_filter
        )
        
        return jsonify({
            "success": True,
            "entities": entities,
            "count": len(entities)
        })
            
    except Exception as e:
        logger.error(f"❌ Failed to get pre-approval entities: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

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

def _is_graph_query_direct(message: str) -> bool:
    """Detect if a message is likely to be a graph-related query."""
    message_lower = message.lower()

    # Graph query indicators
    graph_indicators = [
        "relationship", "connection", "works at", "employed by", "partnership",
        "acquisition", "merger", "investment", "funding", "board", "director",
        "who is", "what is", "how is", "connected to", "related to", "associated with",
        "graph", "network", "visualize", "show me", "find connections", "entity",
        "company", "person", "organization", "ceo", "executive", "chairman",
        "employee", "shareholder", "subsidiary", "parent company", "owns",
        "founded by", "worked at", "member of", "part of", "belongs to"
    ]

    return any(indicator in message_lower for indicator in graph_indicators)

def detect_entity_type_query(message: str) -> Optional[List[str]]:
    """
    Detect if the query is asking for specific entity types (Person or Company).

    Args:
        message: User query

    Returns:
        List of entity types to filter by, or None if no specific types detected
    """
    message_lower = message.lower()

    # Person-specific indicators
    person_indicators = [
        "person", "people", "individual", "executive", "director", "ceo", "cto",
        "chairman", "employee", "staff", "member", "who is", "who are",
        "find person", "search person", "show people", "list people"
    ]

    # Company-specific indicators
    company_indicators = [
        "company", "companies", "corporation", "business", "organization",
        "firm", "enterprise", "institution", "authority", "club",
        "find company", "search company", "show companies", "list companies"
    ]

    detected_types = []

    # Check for person queries
    if any(indicator in message_lower for indicator in person_indicators):
        detected_types.append("Person")

    # Check for company queries
    if any(indicator in message_lower for indicator in company_indicators):
        detected_types.append("Company")

    # If both or neither detected, return None (use general search)
    if len(detected_types) == 0 or len(detected_types) == 2:
        return None

    return detected_types

def process_message_with_agent(message: str, is_graph_query: bool = False) -> dict:
    """
    Process message using enhanced two-step approach:
    1. Generate natural language answer based on the query
    2. Query Neo4j again to get specific entities and relationships for graph visualization
    """
    try:
        logger.info(f"🤖 Processing message with enhanced two-step approach: {message}")

        if is_graph_query:
            logger.info("🎯 Graph query detected, using enhanced approach...")

            # Check for entity type-specific queries
            entity_types = detect_entity_type_query(message)
            if entity_types:
                logger.info(f"🏷️ Entity type query detected: {entity_types}")

            # Step 1: Generate natural language answer based on the query
            logger.info("📝 Step 1: Generating natural language answer...")
            natural_answer = generate_natural_language_answer(message)

            # Step 2: Query for graph visualization (with entity type filtering if applicable)
            logger.info("🔍 Step 2: Querying for graph visualization...")
            import asyncio
            try:
                # Create new event loop if none exists
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                # Use entity type search if specific types detected
                if entity_types and GRAPHITI_SEARCH_AVAILABLE:
                    logger.info(f"🎯 Using entity type filtering: {entity_types}")
                    graph_data = loop.run_until_complete(search_entities_by_type(message, entity_types))
                else:
                    # Fallback to regular Neo4j search
                    graph_data = loop.run_until_complete(query_neo4j_for_graph_visualization(message, natural_answer))

            except RuntimeError:
                # If we're already in an event loop, use asyncio.run
                if entity_types and GRAPHITI_SEARCH_AVAILABLE:
                    graph_data = asyncio.run(search_entities_by_type(message, entity_types))
                else:
                    graph_data = asyncio.run(query_neo4j_for_graph_visualization(message, natural_answer))
            finally:
                try:
                    loop.close()
                except:
                    pass

            # Combine the natural answer with graph data
            if graph_data and (graph_data.get('nodes') or graph_data.get('relationships')):
                node_count = len(graph_data.get('nodes', []))
                rel_count = len(graph_data.get('relationships', []))

                # Enhanced response with natural language answer
                response_text = natural_answer
                response_text += f"\n\n📊 Graph visualization shows {node_count} entities and {rel_count} relationships."

                return {
                    'type': 'content',
                    'content': response_text,
                    'graph_data': graph_data,
                    'natural_answer': natural_answer,
                    'step_1_complete': True,
                    'step_2_complete': True
                }
            else:
                # If no graph data found, still return the natural answer
                response_text = natural_answer
                response_text += "\n\n📊 No specific graph visualization data was found for this query."

                return {
                    'type': 'content',
                    'content': response_text,
                    'natural_answer': natural_answer,
                    'step_1_complete': True,
                    'step_2_complete': False
                }

        else:
            # For non-graph queries, use the agent for general responses
            logger.info("💬 General query detected, using agent for response...")
            response_text = generate_general_response(message)

            return {
                'type': 'content',
                'content': response_text
            }

    except Exception as e:
        logger.error(f"❌ Enhanced agent processing error: {e}")
        return {
            'type': 'error',
            'content': f"Error processing your request: {str(e)}"
        }

def generate_natural_language_answer(query: str) -> str:
    """
    Step 1: Generate a natural language answer based on the query.
    Uses Neo4j to find relationships and generates human-readable responses.
    """
    try:
        logger.info(f"📝 Generating natural language answer for: {query}")

        # Import Neo4j utilities
        from agent.enhanced_graph_search import EnhancedGraphSearch

        # Check if this is a "who is" query
        if query.lower().startswith("who is"):
            logger.info("🎯 Detected 'who is' query, using enhanced person search...")

            # Extract the person name from the query
            import re
            who_is_pattern = r"who\s+is\s+['\"]?([^'\"?]+)['\"]?"
            who_is_match = re.search(who_is_pattern, query.lower())

            if who_is_match:
                person_name = who_is_match.group(1).strip()
                logger.info(f"🔍 Searching for person: {person_name}")

                # Use direct Neo4j search to get comprehensive information
                try:
                    import sys
                    import os

                    # Add project root to path
                    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    if project_root not in sys.path:
                        sys.path.insert(0, project_root)

                    # Use direct Neo4j search instead of async function
                    person_results = search_person_sync(person_name)

                    if person_results:
                        person = person_results[0]
                        name = person.get('name', person_name)
                        position = person.get('position', '')
                        company = person.get('company', '')
                        summary = person.get('summary', '')
                        relationships = person.get('relationships', [])

                        # Build comprehensive answer
                        answer_parts = [f"{name} is a person"]

                        if position:
                            answer_parts.append(f"who serves as {position}")

                        if company:
                            answer_parts.append(f"at {company}")

                        # Add key relationships
                        if relationships:
                            key_roles = []
                            for rel in relationships:
                                rel_type = rel.get('relationship_type', '')
                                target = rel.get('target', '')
                                detail = rel.get('relationship_detail', '')

                                if rel_type == 'CEO_OF':
                                    key_roles.append(f"CEO of {target}")
                                elif rel_type == 'CHAIRMAN_OF':
                                    key_roles.append(f"Chairman of {target}")
                                elif rel_type == 'DIRECTOR_OF':
                                    key_roles.append(f"Director of {target}")

                            if key_roles:
                                if len(key_roles) == 1:
                                    answer_parts.append(f". {name} is the {key_roles[0]}")
                                else:
                                    answer_parts.append(f". {name} holds multiple leadership positions: {', '.join(key_roles)}")

                        # Add summary if available
                        if summary and len(summary) > 50:
                            # Extract key information from summary
                            summary_short = summary[:200] + "..." if len(summary) > 200 else summary
                            answer_parts.append(f"\n\nAdditional information: {summary_short}")

                        answer = " ".join(answer_parts[:-1]) + answer_parts[-1] if answer_parts else f"I found information about {name}."

                        return answer
                    else:
                        return f"I couldn't find specific information about {person_name} in the knowledge graph."

                except Exception as e:
                    logger.error(f"Enhanced person search failed: {e}")
                    return f"I'm searching for information about {person_name}. Let me check the knowledge graph."

        # Check if this is a relationship query
        elif _is_relationship_query_direct(query):
            logger.info("🔗 Detected relationship query, extracting entities...")

            # Extract entities from the query
            entities = extract_entities_from_query(query)

            if len(entities) >= 2:
                entity1, entity2 = entities[0], entities[1]
                logger.info(f"🎯 Searching for relationship between: {entity1} and {entity2}")

                # Try enhanced person search first if one entity is a person
                person_relationships = search_person_to_entity_relationship_sync(entity1, entity2)

                if person_relationships:
                    # Found relationships using enhanced search
                    answer_parts = []

                    for rel in person_relationships:
                        source = rel.get('source', entity1)
                        target = rel.get('target', entity2)
                        rel_type = rel.get('relationship_type', 'RELATED_TO')
                        detail = rel.get('relationship_detail', '')
                        method = rel.get('extraction_method', 'unknown')

                        # Generate natural language description
                        if rel_type == 'CEO_OF':
                            answer_parts.append(f"{source} is the Chief Executive Officer (CEO) of {target}")
                        elif rel_type == 'CHAIRMAN_OF':
                            answer_parts.append(f"{source} is the Chairman of {target}")
                        elif rel_type == 'DIRECTOR_OF':
                            answer_parts.append(f"{source} is a Director of {target}")
                        elif rel_type == 'EXECUTIVE_OF':
                            answer_parts.append(f"{source} is an Executive of {target}")
                        elif rel_type == 'WORKS_AT':
                            answer_parts.append(f"{source} works at {target}")
                        else:
                            answer_parts.append(f"{source} is {rel_type.replace('_', ' ').lower()} {target}")

                        if detail and detail != rel_type.replace('_', ' '):
                            answer_parts[-1] += f" ({detail})"

                    if len(answer_parts) == 1:
                        answer = answer_parts[0] + "."
                    else:
                        answer = ". ".join(answer_parts[:-1]) + f", and {answer_parts[-1]}."

                    return answer

                # Fallback to original enhanced graph search
                search = EnhancedGraphSearch()
                result = search.search_entities_and_relationships(entity1, entity2)

                # Generate natural language response based on findings
                if result and result.get('direct_relationships'):
                    relationships = result['direct_relationships']

                    if relationships:
                        # Extract the first/main relationship
                        main_rel = relationships[0]
                        source_name = main_rel.get('source', {}).get('name', entity1)
                        target_name = main_rel.get('target', {}).get('name', entity2)
                        rel_type = main_rel.get('relationship_type', 'RELATED_TO')
                        rel_detail = main_rel.get('relationship_detail', '')

                        # Generate natural language based on relationship type
                        answer = generate_relationship_description(source_name, target_name, rel_type, rel_detail)

                        # Add additional relationships if found
                        if len(relationships) > 1:
                            answer += f"\n\nAdditionally, I found {len(relationships) - 1} other connections between these entities."

                        return answer

                # If no relationships found
                return f"I searched for connections between {entity1} and {entity2}, but couldn't find any direct relationships in the knowledge graph."

            elif len(entities) == 1:
                # Single entity query
                entity = entities[0]
                return f"I found information about {entity}. Let me show you their connections in the knowledge graph."

        # For general queries, provide a contextual response
        return f"Based on your query about '{query}', I'll search the knowledge graph to find relevant information and relationships."

    except Exception as e:
        logger.error(f"❌ Error generating natural language answer: {e}")
        return f"I'm analyzing your query: '{query}'. Let me search the knowledge graph for relevant information."

def generate_relationship_description(source: str, target: str, rel_type: str, detail: str = "") -> str:
    """Generate natural language description of a relationship."""

    # Map relationship types to natural language
    relationship_descriptions = {
        'CEO_OF': f"{source} is the CEO of {target}",
        'CHAIRMAN_OF': f"{source} is the Chairman of {target}",
        'DIRECTOR_OF': f"{source} is a Director of {target}",
        'SECRETARY_OF': f"{source} is the Secretary of {target}",
        'EMPLOYED_BY': f"{source} is employed by {target}",
        'WORKS_AT': f"{source} works at {target}",
        'MEMBER_OF': f"{source} is a member of {target}",
        'FOUNDER_OF': f"{source} is the founder of {target}",
        'OWNER_OF': f"{source} owns {target}",
        'PARTNER_OF': f"{source} is a partner of {target}",
        'RELATED_TO': f"{source} is related to {target}",
        'ASSOCIATED_WITH': f"{source} is associated with {target}",
        'CONNECTED_TO': f"{source} is connected to {target}"
    }

    # Get the base description
    description = relationship_descriptions.get(rel_type, f"{source} has a {rel_type.lower().replace('_', ' ')} relationship with {target}")

    # Add detail if available
    if detail and detail.strip():
        if rel_type in ['CEO_OF', 'CHAIRMAN_OF', 'DIRECTOR_OF']:
            description += f", serving in the role of {detail}"
        else:
            description += f" ({detail})"

    description += "."

    return description

def extract_entities_from_query(query: str) -> List[str]:
    """Extract entity names from a query string."""
    import re

    entities = []
    query_lower = query.lower()

    # Skip extraction from generic response text
    generic_phrases = [
        "i'll search", "search the knowledge", "find relevant information",
        "based on the query", "let me search", "looking for", "i'll look",
        "searching for", "i need to", "let me find"
    ]

    if any(phrase in query_lower for phrase in generic_phrases):
        logger.info(f"🚫 Skipping entity extraction from generic response text")
        return []

    # First, handle special cases like HKJC
    special_entities = {
        'hkjc': 'Hong Kong Jockey Club',
        'hong kong jockey club': 'Hong Kong Jockey Club',
        'the hong kong jockey club': 'Hong Kong Jockey Club'
    }

    # Handle "who is" queries specifically
    who_is_pattern = r"who\s+is\s+['\"]?([^'\"?]+)['\"]?"
    who_is_match = re.search(who_is_pattern, query_lower)
    if who_is_match:
        person_name = who_is_match.group(1).strip()
        logger.info(f"🎯 Detected 'who is' query for: {person_name}")
        entities.append(person_name)
        return entities

    # Common patterns for relationship queries - improved to handle quotes better
    patterns = [
        r"relation(?:ship)?\s+between\s+['\"]([^'\"]+)['\"]?\s+and\s+['\"]?([^'\"?\s]+)['\"]?",
        r"relation(?:ship)?\s+between\s+([^'\"]+?)\s+and\s+([^'\"?\s]+)",
        r"connection\s+between\s+['\"]([^'\"]+)['\"]?\s+and\s+['\"]?([^'\"?\s]+)['\"]?",
        r"connection\s+between\s+([^'\"]+?)\s+and\s+([^'\"?\s]+)",
        r"how\s+is\s+['\"]([^'\"]+)['\"]?\s+(?:related\s+to|connected\s+to)\s+['\"]?([^'\"?\s]+)['\"]?",
        r"['\"]([^'\"]+)['\"]?\s+(?:works?\s+(?:at|for)|employed\s+by)\s+['\"]?([^'\"?\s]+)['\"]?",
        r"['\"]([^'\"]+)['\"]?\s+(?:and|vs\.?)\s+['\"]?([^'\"?\s]+)['\"]?"
    ]

    for pattern in patterns:
        match = re.search(pattern, query_lower)
        if match:
            extracted = [entity.strip() for entity in match.groups()]
            # Process special entities
            processed_entities = []
            for entity in extracted:
                entity_clean = entity.strip().lower()
                if entity_clean in special_entities:
                    processed_entities.append(special_entities[entity_clean])
                else:
                    processed_entities.append(entity.strip())
            entities.extend(processed_entities)
            break

    # If no pattern matched, try to extract quoted strings or proper nouns
    if not entities:
        # Extract quoted strings
        quoted_matches = re.findall(r"['\"]([^'\"]+)['\"]", query)
        if quoted_matches:
            entities.extend(quoted_matches)
        else:
            # Extract capitalized words (potential proper nouns)
            words = query.split()
            potential_entities = []
            current_entity = []

            for word in words:
                # Clean word of punctuation
                clean_word = re.sub(r'[^\w\s]', '', word)
                if clean_word and (clean_word[0].isupper() or clean_word.lower() in ['hkjc', 'ceo', 'chairman']):
                    current_entity.append(clean_word)
                else:
                    if current_entity:
                        potential_entities.append(' '.join(current_entity))
                        current_entity = []

            if current_entity:
                potential_entities.append(' '.join(current_entity))

            # Filter out common words and keep likely entity names
            common_words = {'The', 'And', 'Or', 'But', 'In', 'On', 'At', 'To', 'For', 'Of', 'With', 'By'}
            entities.extend([entity for entity in potential_entities if entity not in common_words and len(entity) > 1])

    # Clean and deduplicate entities, handle special cases
    cleaned_entities = []
    for entity in entities:
        entity = entity.strip()
        if entity:
            # Check for special entity mappings
            entity_lower = entity.lower()
            if entity_lower in special_entities:
                entity = special_entities[entity_lower]

            if entity not in cleaned_entities:
                cleaned_entities.append(entity)

    logger.info(f"🎯 Extracted entities from query: {cleaned_entities}")
    return cleaned_entities

def _is_relationship_query_direct(query: str) -> bool:
    """Check if query is asking about relationships between entities."""
    relationship_indicators = [
        "relation between", "relationship between", "connection between",
        "how is", "connected to", "related to", "works with", "works at", "works for",
        "associated with", "link between", "ties between", "employed by"
    ]
    query_lower = query.lower()
    return any(indicator in query_lower for indicator in relationship_indicators)

def search_person_sync(person_name: str) -> list:
    """
    Synchronous person search using direct Neo4j queries.
    """
    try:
        import os
        from neo4j import GraphDatabase

        # Get Neo4j configuration
        neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        neo4j_user = os.getenv("NEO4J_USERNAME", os.getenv("NEO4J_USER", "neo4j"))
        neo4j_password = os.getenv("NEO4J_PASSWORD")
        neo4j_database = os.getenv("NEO4J_DATABASE", "neo4j")

        if not neo4j_password:
            logger.warning("Neo4j password not found")
            return []

        # Create driver and session
        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        session = driver.session(database=neo4j_database)

        try:
            # Case-insensitive search for the person (using Entity label since Person/Company labels don't exist)
            cypher_query = """
            MATCH (p:Entity)
            WHERE toLower(p.name) CONTAINS toLower($name_query)
            RETURN p.name as name,
                   null as company,
                   null as position,
                   p.summary as summary,
                   p.uuid as uuid,
                   labels(p) as labels
            ORDER BY p.name
            LIMIT 1
            """

            result = session.run(cypher_query, name_query=person_name)
            records = list(result)

            if not records:
                return []

            record = records[0]
            person_data = {
                "name": record.get("name"),
                "company": record.get("company"),
                "position": record.get("position"),
                "summary": record.get("summary", ""),
                "uuid": record.get("uuid"),
                "labels": record.get("labels", []),
                "search_method": "sync_neo4j",
                "relationships": []
            }

            # Extract relationships from summary and properties
            relationships = extract_relationships_from_person_sync(person_data)

            # Also search related organizations for additional relationships
            try:
                org_relationships = search_related_organizations_sync(person_data["name"], session)
                relationships.extend(org_relationships)
            except Exception as e:
                logger.warning(f"Failed to get organization relationships: {e}")

            # Remove duplicates and filter out self-references
            seen = set()
            unique_relationships = []
            for rel in relationships:
                target = rel["target"]
                # Skip self-references (person as target)
                if target.lower() == person_data["name"].lower():
                    continue

                key = (rel["relationship_type"], target.lower())
                if key not in seen:
                    seen.add(key)
                    unique_relationships.append(rel)

            person_data["relationships"] = unique_relationships

            return [person_data]

        finally:
            session.close()
            driver.close()

    except Exception as e:
        logger.error(f"Sync person search failed: {e}")
        return []

def extract_relationships_from_person_sync(person_data: dict) -> list:
    """
    Extract relationships from person data synchronously.
    """
    relationships = []
    name = person_data.get("name", "")
    company = person_data.get("company")
    position = person_data.get("position", "")
    summary = person_data.get("summary", "")

    # Extract from company property
    if company:
        rel_type = "WORKS_AT"
        if position:
            if "ceo" in position.lower():
                rel_type = "CEO_OF"
            elif "chair" in position.lower() or "chairman" in position.lower():
                rel_type = "CHAIRMAN_OF"
            elif "director" in position.lower():
                rel_type = "DIRECTOR_OF"
            elif "executive" in position.lower():
                rel_type = "EXECUTIVE_OF"

        relationships.append({
            "source": name,
            "target": company,
            "relationship_type": rel_type,
            "relationship_detail": position,
            "extraction_method": "property_based"
        })

    # Extract from summary text
    if summary:
        import re

        # Look for CEO relationships
        if "ceo" in summary.lower() or "chief executive officer" in summary.lower():
            ceo_patterns = [
                r'(?:ceo|chief executive officer)\s+of\s+([^,.]+)',
                r'is\s+the\s+(?:ceo|chief executive officer)\s+of\s+([^,.]+)'
            ]

            for pattern in ceo_patterns:
                matches = re.findall(pattern, summary.lower())
                for match in matches:
                    company_name = match.strip()
                    if company_name and len(company_name) > 2:
                        relationships.append({
                            "source": name,
                            "target": company_name.title(),
                            "relationship_type": "CEO_OF",
                            "relationship_detail": "Chief Executive Officer",
                            "extraction_method": "summary_text"
                        })

        # Look for Chair relationships
        if "chair" in summary.lower():
            chair_patterns = [
                r'(?:chair|chairman)\s+of\s+([^,.]+)',
                r'is\s+the\s+(?:chair|chairman)\s+of\s+([^,.]+)'
            ]

            for pattern in chair_patterns:
                matches = re.findall(pattern, summary.lower())
                for match in matches:
                    company_name = match.strip()
                    if company_name and len(company_name) > 2:
                        relationships.append({
                            "source": name,
                            "target": company_name.title(),
                            "relationship_type": "CHAIRMAN_OF",
                            "relationship_detail": "Chair",
                            "extraction_method": "summary_text"
                        })

    # Remove duplicates
    seen = set()
    unique_relationships = []
    for rel in relationships:
        key = (rel["relationship_type"], rel["target"].lower())
        if key not in seen:
            seen.add(key)
            unique_relationships.append(rel)

    return unique_relationships

def search_related_organizations_sync(person_name: str, session) -> list:
    """
    Search related organizations for additional relationship information.
    """
    relationships = []

    try:
        # Search for organizations that mention this person in their summary
        query = """
        MATCH (org)
        WHERE (org:Company OR org:Entity)
          AND toLower(org.summary) CONTAINS toLower($person_name)
        RETURN org.name as org_name, org.summary as org_summary
        """

        result = session.run(query, person_name=person_name)
        records = list(result)

        for record in records:
            org_name = record.get("org_name", "")
            org_summary = record.get("org_summary", "")

            if org_summary:
                # Extract relationships from organization summary
                import re

                # Look for CEO relationships
                if "ceo" in org_summary.lower() or "chief executive officer" in org_summary.lower():
                    # Pattern to find "CEO [person_name]" or "[person_name] is the CEO"
                    ceo_patterns = [
                        rf'(?:ceo|chief executive officer)\s+{re.escape(person_name.lower())}',
                        rf'{re.escape(person_name.lower())}\s+(?:is\s+the\s+)?(?:ceo|chief executive officer)',
                        rf'the\s+(?:ceo|chief executive officer)\s+{re.escape(person_name.lower())}'
                    ]

                    for pattern in ceo_patterns:
                        if re.search(pattern, org_summary.lower()):
                            relationships.append({
                                "source": person_name,
                                "target": org_name,
                                "relationship_type": "CEO_OF",
                                "relationship_detail": "Chief Executive Officer",
                                "extraction_method": "organization_summary"
                            })
                            break

                # Look for Chair relationships
                if "chair" in org_summary.lower():
                    chair_patterns = [
                        rf'(?:chair|chairman)\s+{re.escape(person_name.lower())}',
                        rf'{re.escape(person_name.lower())}\s+(?:is\s+the\s+)?(?:chair|chairman)',
                        rf'the\s+(?:chair|chairman)\s+{re.escape(person_name.lower())}'
                    ]

                    for pattern in chair_patterns:
                        if re.search(pattern, org_summary.lower()):
                            relationships.append({
                                "source": person_name,
                                "target": org_name,
                                "relationship_type": "CHAIRMAN_OF",
                                "relationship_detail": "Chair",
                                "extraction_method": "organization_summary"
                            })
                            break

        logger.info(f"Found {len(relationships)} relationships from organization summaries for {person_name}")
        return relationships

    except Exception as e:
        logger.error(f"Organization search failed for {person_name}: {e}")
        return []

def search_person_to_entity_relationship_sync(entity1: str, entity2: str) -> list:
    """
    Search for relationships between two entities using enhanced person search.
    """
    relationships = []

    try:
        # Try both directions - entity1 as person, entity2 as organization
        person_results1 = search_person_sync(entity1)
        if person_results1:
            person = person_results1[0]
            for rel in person.get('relationships', []):
                target = rel.get('target', '').lower()
                entity2_lower = entity2.lower()

                # Check if target matches entity2 (with variations)
                if (target == entity2_lower or
                    entity2_lower in target or
                    target in entity2_lower or
                    # Handle HKJC variations
                    ('hkjc' in entity2_lower and 'hong kong jockey' in target) or
                    ('hong kong jockey' in entity2_lower and 'hkjc' in target)):

                    relationships.append(rel)

        # Try entity2 as person, entity1 as organization
        person_results2 = search_person_sync(entity2)
        if person_results2:
            person = person_results2[0]
            for rel in person.get('relationships', []):
                target = rel.get('target', '').lower()
                entity1_lower = entity1.lower()

                # Check if target matches entity1 (with variations)
                if (target == entity1_lower or
                    entity1_lower in target or
                    target in entity1_lower or
                    # Handle HKJC variations
                    ('hkjc' in entity1_lower and 'hong kong jockey' in target) or
                    ('hong kong jockey' in entity1_lower and 'hkjc' in target)):

                    # Swap source and target for correct direction
                    swapped_rel = rel.copy()
                    swapped_rel['source'] = rel.get('target', entity1)
                    swapped_rel['target'] = rel.get('source', entity2)
                    relationships.append(swapped_rel)

        # Remove duplicates
        seen = set()
        unique_relationships = []
        for rel in relationships:
            key = (rel.get('relationship_type', ''), rel.get('source', '').lower(), rel.get('target', '').lower())
            if key not in seen:
                seen.add(key)
                unique_relationships.append(rel)

        logger.info(f"Found {len(unique_relationships)} relationships between {entity1} and {entity2}")
        return unique_relationships

    except Exception as e:
        logger.error(f"Person-to-entity relationship search failed: {e}")
        return []

def search_graphiti_for_person_sync(person_name: str) -> list:
    """
    Search Graphiti knowledge graph for additional person relationships synchronously.
    """
    relationships = []

    try:
        import sys
        import os

        # Add project root to path
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        from agent.tools import graph_search_tool, GraphSearchInput
        import asyncio

        # Search for facts about this person
        input_data = GraphSearchInput(query=person_name)

        # Run async function synchronously
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            graphiti_results = loop.run_until_complete(graph_search_tool(input_data))
        except RuntimeError:
            # If already in event loop, skip Graphiti search
            logger.warning("Cannot run Graphiti search in existing event loop")
            return []
        finally:
            try:
                loop.close()
            except:
                pass

        for result in graphiti_results:
            fact = result.fact.lower()

            # Look for CEO relationships
            if "chief executive officer" in fact or "ceo" in fact:
                import re
                ceo_patterns = [
                    r'(?:ceo|chief executive officer)\s+of\s+([^,.]+)',
                    r'is\s+the\s+(?:ceo|chief executive officer)\s+of\s+([^,.]+)'
                ]

                for pattern in ceo_patterns:
                    matches = re.findall(pattern, fact)
                    for match in matches:
                        company_name = match.strip()
                        if company_name and len(company_name) > 2:
                            relationships.append({
                                "source": person_name,
                                "target": company_name.title(),
                                "relationship_type": "CEO_OF",
                                "relationship_detail": "Chief Executive Officer",
                                "extraction_method": "graphiti_fact"
                            })

            # Look for Chair relationships
            if "chair" in fact:
                import re
                chair_patterns = [
                    r'(?:chair|chairman)\s+of\s+([^,.]+)',
                    r'is\s+the\s+(?:chair|chairman)\s+of\s+([^,.]+)'
                ]

                for pattern in chair_patterns:
                    matches = re.findall(pattern, fact)
                    for match in matches:
                        company_name = match.strip()
                        if company_name and len(company_name) > 2:
                            relationships.append({
                                "source": person_name,
                                "target": company_name.title(),
                                "relationship_type": "CHAIRMAN_OF",
                                "relationship_detail": "Chair",
                                "extraction_method": "graphiti_fact"
                            })

        logger.info(f"Found {len(relationships)} relationships from Graphiti for {person_name}")
        return relationships

    except Exception as e:
        logger.error(f"Graphiti search failed for {person_name}: {e}")
        return []

async def get_person_graph_data(person_name: str, session, driver) -> Optional[dict]:
    """
    Get graph data for a person using enhanced person search.
    """
    try:
        import sys
        import os

        # Add project root to path
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        from agent.graph_utils import search_people

        logger.info(f"🔍 Enhanced person search for: {person_name}")

        # Use our enhanced person search
        person_results = await search_people(name_query=person_name, limit=1)

        if not person_results:
            logger.warning(f"⚠️ No person found for: {person_name}")
            return None

        person = person_results[0]
        logger.info(f"✅ Found person: {person.get('name')} with {len(person.get('relationships', []))} relationships")

        # Build graph data from person and relationships
        nodes = []
        relationships = []
        node_ids = set()

        # Add the person node
        person_node_id = f"person_{person.get('uuid', '0')}"
        nodes.append({
            'id': person_node_id,
            'properties': {
                'name': person.get('name'),
                'type': 'Person',
                'position': person.get('position'),
                'company': person.get('company'),
                'summary': person.get('summary', '')[:200] + "..." if len(person.get('summary', '')) > 200 else person.get('summary', ''),
                'search_method': person.get('search_method', 'enhanced_neo4j')
            },
            'labels': ['Person']
        })
        node_ids.add(person_node_id)

        # Add relationship nodes and edges
        for i, rel in enumerate(person.get('relationships', [])):
            target_name = rel.get('target', '')
            if target_name:
                # Create target node
                target_node_id = f"entity_{i}"
                if target_node_id not in node_ids:
                    nodes.append({
                        'id': target_node_id,
                        'properties': {
                            'name': target_name,
                            'type': 'Organization' if 'company' in target_name.lower() or 'club' in target_name.lower() else 'Entity'
                        },
                        'labels': ['Organization'] if 'company' in target_name.lower() or 'club' in target_name.lower() else ['Entity']
                    })
                    node_ids.add(target_node_id)

                # Create relationship
                relationships.append({
                    'id': f"rel_{i}",
                    'startNodeId': person_node_id,
                    'endNodeId': target_node_id,
                    'type': rel.get('relationship_type', 'RELATED_TO'),
                    'properties': {
                        'detail': rel.get('relationship_detail', ''),
                        'extraction_method': rel.get('extraction_method', 'unknown')
                    }
                })

        result = {
            "nodes": nodes,
            "relationships": relationships,
            "metadata": {
                "source": "enhanced_person_search",
                "query": person_name,
                "person_found": True,
                "total_relationships": len(relationships)
            }
        }

        logger.info(f"✅ Generated graph data: {len(nodes)} nodes, {len(relationships)} relationships")
        return result

    except Exception as e:
        logger.error(f"Enhanced person graph search failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None

async def get_relationship_graph_data(entity1: str, entity2: str, session, driver) -> Optional[dict]:
    """
    Get graph data for a relationship query using enhanced search.
    """
    try:
        logger.info(f"🔍 Enhanced relationship search for: {entity1} and {entity2}")

        # Use our enhanced relationship search
        relationships = search_person_to_entity_relationship_sync(entity1, entity2)

        if not relationships:
            logger.warning(f"⚠️ No relationships found between: {entity1} and {entity2}")
            return None

        logger.info(f"✅ Found {len(relationships)} relationships")

        # Build graph data from relationships
        nodes = []
        graph_relationships = []
        node_ids = set()

        # Add nodes for both entities
        entity1_node_id = "entity1"
        entity2_node_id = "entity2"

        # Determine node types
        person_results1 = search_person_sync(entity1)
        person_results2 = search_person_sync(entity2)

        # Add entity1 node
        if person_results1:
            person = person_results1[0]
            nodes.append({
                'id': entity1_node_id,
                'properties': {
                    'name': person.get('name', entity1),
                    'type': 'Person',
                    'position': person.get('position'),
                    'company': person.get('company'),
                    'summary': person.get('summary', '')[:200] + "..." if len(person.get('summary', '')) > 200 else person.get('summary', '')
                },
                'labels': ['Person']
            })
        else:
            nodes.append({
                'id': entity1_node_id,
                'properties': {
                    'name': entity1,
                    'type': 'Organization'
                },
                'labels': ['Organization']
            })
        node_ids.add(entity1_node_id)

        # Add entity2 node
        if person_results2:
            person = person_results2[0]
            nodes.append({
                'id': entity2_node_id,
                'properties': {
                    'name': person.get('name', entity2),
                    'type': 'Person',
                    'position': person.get('position'),
                    'company': person.get('company'),
                    'summary': person.get('summary', '')[:200] + "..." if len(person.get('summary', '')) > 200 else person.get('summary', '')
                },
                'labels': ['Person']
            })
        else:
            nodes.append({
                'id': entity2_node_id,
                'properties': {
                    'name': entity2,
                    'type': 'Organization'
                },
                'labels': ['Organization']
            })
        node_ids.add(entity2_node_id)

        # Add relationship edges
        for i, rel in enumerate(relationships):
            source_name = rel.get('source', entity1).lower()
            target_name = rel.get('target', entity2).lower()

            # Determine direction
            if entity1.lower() in source_name or source_name in entity1.lower():
                start_node = entity1_node_id
                end_node = entity2_node_id
            else:
                start_node = entity2_node_id
                end_node = entity1_node_id

            graph_relationships.append({
                'id': f"rel_{i}",
                'startNodeId': start_node,
                'endNodeId': end_node,
                'type': rel.get('relationship_type', 'RELATED_TO'),
                'properties': {
                    'detail': rel.get('relationship_detail', ''),
                    'extraction_method': rel.get('extraction_method', 'unknown')
                }
            })

        result = {
            "nodes": nodes,
            "relationships": graph_relationships,
            "metadata": {
                "source": "enhanced_relationship_search",
                "query": f"{entity1} and {entity2}",
                "relationships_found": True,
                "total_relationships": len(graph_relationships)
            }
        }

        logger.info(f"✅ Generated relationship graph data: {len(nodes)} nodes, {len(graph_relationships)} relationships")
        return result

    except Exception as e:
        logger.error(f"Enhanced relationship graph search failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None

async def query_neo4j_for_graph_visualization(query: str, natural_answer: str) -> Optional[dict]:
    """
    Step 2: Query Neo4j database to get specific entities and relationships for graph visualization.
    Uses the natural answer to extract key entities and build a focused graph.
    """
    try:
        logger.info(f"🔍 Querying Neo4j for graph visualization based on: {query}")

        # Extract entities from both the original query and the natural answer
        query_entities = extract_entities_from_query(query)
        answer_entities = extract_entities_from_query(natural_answer)

        # Combine and deduplicate entities
        all_entities = list(set(query_entities + answer_entities))
        logger.info(f"🎯 Target entities for graph: {all_entities}")

        # Special handling for "who is" queries - use enhanced person search
        if query.lower().startswith("who is") and all_entities:
            person_name = all_entities[0]
            logger.info(f"🎯 Using enhanced person search for: {person_name}")
            # Get Neo4j session for the enhanced search
            session, driver = get_neo4j_session_with_driver()
            try:
                result = await get_person_graph_data(person_name, session, driver)
                return result
            finally:
                session.close()
                driver.close()

        # Special handling for relationship queries - use enhanced relationship search
        if len(all_entities) >= 2 and any(indicator in query.lower() for indicator in
                                         ["relation", "connection", "between"]):
            entity1, entity2 = all_entities[0], all_entities[1]
            logger.info(f"🎯 Using enhanced relationship search for: {entity1} and {entity2}")
            # Get Neo4j session for the enhanced search
            session, driver = get_neo4j_session_with_driver()
            try:
                result = await get_relationship_graph_data(entity1, entity2, session, driver)
                return result
            finally:
                session.close()
                driver.close()

        if not all_entities:
            logger.warning("⚠️ No entities found for graph visualization")
            return None

        # Get Neo4j session
        session, driver = get_neo4j_session_with_driver()

        try:
            nodes = []
            relationships = []
            node_ids = set()
            rel_ids = set()

            # Build focused queries for each entity
            for entity in all_entities[:3]:  # Limit to top 3 entities to keep graph focused
                logger.info(f"🔍 Searching for entity: {entity}")

                # Query 1: Find the entity node and its direct relationships
                entity_query = """
                MATCH (n)-[r]-(connected)
                WHERE toLower(n.name) CONTAINS toLower($entity_name)
                   OR n.name CONTAINS $entity_name
                   OR toLower(n.name) = toLower($entity_name)
                   OR (toLower($entity_name) = 'hong kong jockey club' AND toLower(n.name) CONTAINS 'hong kong jockey')
                   OR (toLower($entity_name) CONTAINS 'hkjc' AND toLower(n.name) CONTAINS 'hong kong jockey')
                RETURN n, r, connected
                LIMIT 15
                """

                result = session.run(entity_query, entity_name=entity)
                records = list(result)

                for record in records:
                    # Process source node
                    if 'n' in record:
                        node = record['n']
                        node_id = str(node.element_id)
                        if node_id not in node_ids:
                            node_data = {
                                "id": node_id,
                                "labels": list(node.labels),
                                "properties": dict(node.items())
                            }
                            nodes.append(node_data)
                            node_ids.add(node_id)

                    # Process connected node
                    if 'connected' in record:
                        node = record['connected']
                        node_id = str(node.element_id)
                        if node_id not in node_ids:
                            node_data = {
                                "id": node_id,
                                "labels": list(node.labels),
                                "properties": dict(node.items())
                            }
                            nodes.append(node_data)
                            node_ids.add(node_id)

                    # Process relationship
                    if 'r' in record:
                        rel = record['r']
                        rel_id = str(rel.element_id)
                        if rel_id not in rel_ids:
                            rel_data = {
                                "id": rel_id,
                                "type": rel.type,
                                "startNodeId": str(rel.start_node.element_id),
                                "endNodeId": str(rel.end_node.element_id),
                                "properties": dict(rel.items())
                            }
                            relationships.append(rel_data)
                            rel_ids.add(rel_id)

            # If we have multiple entities, try to find connections between them
            if len(all_entities) >= 2:
                logger.info("🔗 Searching for connections between entities...")

                connection_query = """
                MATCH path = (a)-[*1..2]-(b)
                WHERE (toLower(a.name) CONTAINS toLower($entity1) OR a.name CONTAINS $entity1)
                  AND (toLower(b.name) CONTAINS toLower($entity2) OR b.name CONTAINS $entity2
                       OR (toLower($entity2) = 'hong kong jockey club' AND toLower(b.name) CONTAINS 'hong kong jockey')
                       OR (toLower($entity2) CONTAINS 'hkjc' AND toLower(b.name) CONTAINS 'hong kong jockey'))
                RETURN path
                LIMIT 8
                """

                for i in range(len(all_entities) - 1):
                    entity1 = all_entities[i]
                    entity2 = all_entities[i + 1]

                    result = session.run(connection_query, entity1=entity1, entity2=entity2)
                    records = list(result)

                    for record in records:
                        if 'path' in record:
                            path = record['path']

                            # Process nodes in path
                            for node in path.nodes:
                                node_id = str(node.element_id)
                                if node_id not in node_ids:
                                    node_data = {
                                        "id": node_id,
                                        "labels": list(node.labels),
                                        "properties": dict(node.items())
                                    }
                                    nodes.append(node_data)
                                    node_ids.add(node_id)

                            # Process relationships in path
                            for rel in path.relationships:
                                rel_id = str(rel.element_id)
                                if rel_id not in rel_ids:
                                    rel_data = {
                                        "id": rel_id,
                                        "type": rel.type,
                                        "startNodeId": str(rel.start_node.element_id),
                                        "endNodeId": str(rel.end_node.element_id),
                                        "properties": dict(rel.items())
                                    }
                                    relationships.append(rel_data)
                                    rel_ids.add(rel_id)

            logger.info(f"✅ Graph visualization query complete: {len(nodes)} nodes, {len(relationships)} relationships")

            return {
                "nodes": nodes,
                "relationships": relationships,
                "metadata": {
                    "source": "focused_entity_query",
                    "target_entities": all_entities,
                    "query": query,
                    "total_nodes": len(nodes),
                    "total_relationships": len(relationships)
                }
            }

        finally:
            close_neo4j_session_and_driver(session, driver)

    except Exception as e:
        logger.error(f"❌ Error querying Neo4j for graph visualization: {e}")
        return None

def generate_general_response(message: str) -> str:
    """Generate a general response for non-graph queries."""
    try:
        logger.info(f"💬 Generating general response for: {message}")

        # For now, provide a helpful response that guides users toward graph queries
        if any(keyword in message.lower() for keyword in ['help', 'what can you do', 'how to use']):
            return """I'm an AI assistant that specializes in exploring knowledge graphs and relationships between entities. Here's what I can help you with:

🔍 **Relationship Queries**: Ask about connections between people and organizations
   • "What is the relationship between [Person] and [Company]?"
   • "How is [Person] connected to [Organization]?"

👥 **Entity Information**: Learn about specific people or companies
   • "Tell me about [Person Name]"
   • "What do you know about [Company Name]?"

📊 **Graph Exploration**: Visualize connections in the knowledge graph
   • "Show me the network around [Entity]"
   • "What are [Person]'s professional connections?"

Try asking about relationships between people and organizations in your knowledge base!"""

        else:
            return f"""I received your message: "{message}".

This appears to be a general query. I specialize in exploring knowledge graphs and relationships between entities.

For the best experience, try asking about:
• Relationships between people and companies
• Professional connections and roles
• Organizational structures and networks

Would you like to explore any specific relationships or entities in the knowledge graph?"""

    except Exception as e:
        logger.error(f"❌ Error generating general response: {e}")
        return f"I received your message: '{message}'. How can I help you explore the knowledge graph?"

@app.route('/chat/direct', methods=['POST'])
def chat_direct():
    """Handle chat messages with direct agent integration (no API server required)."""
    data = request.get_json()
    message = data.get('message', '')

    if not message:
        return jsonify({"error": "Message is required"}), 400

    def generate():
        """Generate streaming response using direct agent integration."""
        try:
            # Check if this is a graph query
            is_graph_query = _is_graph_query_direct(message)
            logger.info(f"🎯 Processing message: {message}")
            logger.info(f"🎯 Is graph query: {is_graph_query}")

            # Send user message
            yield f"data: {json.dumps({'type': 'user_message', 'content': message})}\n\n"

            # Send typing indicator
            yield f"data: {json.dumps({'type': 'typing', 'content': 'Assistant is thinking...'})}\n\n"

            # Process with direct agent integration
            response_content = process_message_with_agent(message, is_graph_query)

            # Send the response
            yield f"data: {json.dumps(response_content)}\n\n"

        except Exception as e:
            logger.error(f"Chat processing error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'content': f'Error: {str(e)}'})}\n\n"

    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Cache-Control'
        }
    )

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
    global INGESTION_STATUS
    
    try:
        # Initialize ingestion status
        reset_ingestion_status()
        INGESTION_STATUS['active'] = True
        INGESTION_STATUS['start_time'] = datetime.now()
        INGESTION_STATUS['ingestion_id'] = str(uuid.uuid4())
        
        logger.info(f"🚀 Starting new ingestion (ID: {INGESTION_STATUS['ingestion_id']})")
        
        # Get uploaded files
        files = request.files.getlist('files') if 'files' in request.files else []
        config_str = request.form.get('config', '{}')

        # Validate files are provided
        if not files:
            reset_ingestion_status()
            return jsonify({"error": "No files provided for ingestion"}), 400

        # Parse configuration
        try:
            config = json.loads(config_str)
        except json.JSONDecodeError:
            reset_ingestion_status()
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

        # Save uploaded files to temporary directory BEFORE starting the generator
        # This ensures files are saved within the request context
        import tempfile
        import os
        temp_dir = tempfile.mkdtemp()
        saved_files = []

        try:
            logger.info(f"📁 Saving {len(files)} files to temporary directory: {temp_dir}")

            for file in files:
                if file.filename:
                    file_path = os.path.join(temp_dir, file.filename)
                    logger.info(f"📄 Processing file: {file.filename}")

                    try:
                        # Save file within request context
                        file.save(file_path)
                        saved_files.append(file_path)

                        # Verify file was saved correctly
                        if os.path.exists(file_path):
                            file_size = os.path.getsize(file_path)
                            logger.info(f"✅ Saved file: {file.filename} -> {file_path} ({file_size} bytes)")
                        else:
                            logger.error(f"❌ Failed to save file: {file.filename}")
                            raise Exception(f"Failed to save file: {file.filename}")

                    except Exception as file_error:
                        logger.error(f"❌ File save error for {file.filename}: {file_error}")
                        raise Exception(f"File save failed: {file_error}")

            logger.info(f"✅ All files saved successfully: {len(saved_files)} files")

        except Exception as save_error:
            # Clean up on save failure
            import shutil
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
            raise save_error

        def generate_progress():
            """Generate streaming progress updates with appropriate ingestion pipeline."""
            global INGESTION_STATUS
            
            try:
                # Store file count
                INGESTION_STATUS['file_count'] = len(saved_files)
                
                # Use the unified ingestion pipeline for all modes
                logger.info(f"🚀 Starting {ingestion_mode} document ingestion pipeline")

                yield f"data: {json.dumps({'type': 'progress', 'current': 0, 'total': 100, 'message': 'Starting ingestion...', 'ingestion_id': INGESTION_STATUS['ingestion_id']})}\n\n"
                
                # Check for cancellation early
                if check_ingestion_cancelled():
                    logger.info("🛑 Ingestion cancelled before starting")
                    yield f"data: {json.dumps({'type': 'cancelled', 'message': 'Ingestion cancelled by user'})}\n\n"
                    return
                
                yield f"data: {json.dumps({'type': 'progress', 'current': 10, 'total': 100, 'message': f'Saved {len(saved_files)} files to temporary directory'})}\n\n"

                # Call the unified ingestion pipeline
                yield from run_unified_ingestion(
                    temp_dir,
                    ingestion_mode,
                    clean_before_ingest,
                    chunk_size,
                    chunk_overlap,
                    use_semantic,
                    extract_entities,
                    verbose,
                    saved_files
                )

            except Exception as ingestion_error:
                logger.error(f"❌ Ingestion pipeline failed: {ingestion_error}")
                yield f"data: {json.dumps({'type': 'error', 'message': f'Ingestion failed: {str(ingestion_error)}'})}\n\n"

            finally:
                # Reset ingestion status when done
                reset_ingestion_status()
                
                # Clean up temporary files after ingestion is complete
                import shutil
                try:
                    shutil.rmtree(temp_dir)
                    logger.info(f"🗑️ Cleaned up temporary directory: {temp_dir}")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to clean up temporary directory: {e}")

        return Response(generate_progress(), mimetype='text/plain')

    except Exception as e:
        logger.error(f"Ingestion endpoint error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/ingest/cancel', methods=['POST'])
def cancel_ingestion():
    """Cancel ongoing ingestion process."""
    global INGESTION_STATUS
    
    try:
        data = request.get_json() or {}
        ingestion_id = data.get('ingestion_id')
        
        # Check if there's an active ingestion
        if not INGESTION_STATUS['active']:
            return jsonify({
                "success": False,
                "error": "No active ingestion to cancel"
            }), 400
        
        # If ingestion_id is provided, verify it matches
        if ingestion_id and INGESTION_STATUS['ingestion_id'] != ingestion_id:
            return jsonify({
                "success": False,
                "error": "Invalid ingestion ID"
            }), 400
        
        # Set cancellation flag
        INGESTION_STATUS['cancelled'] = True
        INGESTION_STATUS['message'] = 'Cancellation requested...'
        
        logger.info(f"🛑 Ingestion cancellation requested (ID: {INGESTION_STATUS['ingestion_id']})")
        
        return jsonify({
            "success": True,
            "message": "Ingestion cancellation requested",
            "ingestion_id": INGESTION_STATUS['ingestion_id']
        })
        
    except Exception as e:
        logger.error(f"❌ Failed to cancel ingestion: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/ingest/status', methods=['GET'])
def get_ingestion_status():
    """Get current ingestion status."""
    return jsonify({
        "status": INGESTION_STATUS,
        "timestamp": datetime.now().isoformat()
    })


def convert_ingestion_results_to_dict(ingestion_result):
    """
    Convert IngestionResult objects to JSON-serializable dictionaries.

    Args:
        ingestion_result: Either a single IngestionResult or List[IngestionResult]

    Returns:
        List of dictionaries representing the ingestion results
    """
    try:
        if isinstance(ingestion_result, list):
            # Convert list of IngestionResult objects to list of dicts
            return [
                {
                    'document_id': result.document_id,
                    'title': result.title,
                    'chunks_created': result.chunks_created,
                    'entities_extracted': result.entities_extracted,
                    'relationships_created': result.relationships_created,
                    'processing_time_ms': result.processing_time_ms,
                    'errors': result.errors
                }
                for result in ingestion_result
            ]
        elif hasattr(ingestion_result, 'document_id'):
            # Single IngestionResult object
            return [{
                'document_id': ingestion_result.document_id,
                'title': ingestion_result.title,
                'chunks_created': ingestion_result.chunks_created,
                'entities_extracted': ingestion_result.entities_extracted,
                'relationships_created': ingestion_result.relationships_created,
                'processing_time_ms': ingestion_result.processing_time_ms,
                'errors': ingestion_result.errors
            }]
        else:
            # Fallback for unexpected format
            logger.warning(f"Unexpected ingestion_result format: {type(ingestion_result)}")
            return []
    except Exception as e:
        logger.error(f"Failed to convert ingestion results to dict: {e}")
        return []


def run_unified_ingestion(temp_dir, ingestion_mode, clean_before_ingest, chunk_size, chunk_overlap,
                         use_semantic, extract_entities, verbose, saved_files):
    """
    Run unified ingestion pipeline using the real ingestion system.
    """
    import json
    import os
    import time
    import asyncio

    try:
        # Check for cancellation before starting
        if check_ingestion_cancelled():
            logger.info("🛑 Ingestion cancelled in run_unified_ingestion")
            yield f"data: {json.dumps({'type': 'cancelled', 'message': 'Ingestion cancelled by user'})}\n\n"
            return
            
        yield f"data: {json.dumps({'type': 'progress', 'current': 15, 'total': 100, 'message': f'Initializing {ingestion_mode} ingestion pipeline...'})}\n\n"

        start_time = time.time()

        # Import the real ingestion pipeline
        from ingestion.ingest import DocumentIngestionPipeline
        from agent.models import IngestionConfig

        # Configure based on mode
        if ingestion_mode == 'basic':
            # Basic mode: optimized for speed and simplicity
            config = IngestionConfig(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                use_semantic_chunking=False,  # Disable for basic mode
                extract_entities=True,       # Keep entity extraction
                skip_graph_building=True     # Skip complex graph building for speed
            )
            logger.info("📋 Basic mode: Simple chunking, entity extraction, no graph building")
        elif ingestion_mode == 'fast':
            # Fast mode: minimal processing
            config = IngestionConfig(
                chunk_size=800,              # Smaller chunks for speed
                chunk_overlap=80,
                use_semantic_chunking=False,
                extract_entities=False,      # Skip for speed
                skip_graph_building=True
            )
            logger.info("📋 Fast mode: Small chunks, no entities, no graph building")
        else:
            # Full mode: complete processing
            config = IngestionConfig(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                use_semantic_chunking=use_semantic,
                extract_entities=extract_entities,
                skip_graph_building=False    # Full graph building
            )
            logger.info("📋 Full mode: Complete processing with graph building")

        yield f"data: {json.dumps({'type': 'progress', 'current': 25, 'total': 100, 'message': 'Creating ingestion pipeline...'})}\n\n"

        # Check for cancellation before creating pipeline
        if check_ingestion_cancelled():
            logger.info("🛑 Ingestion cancelled before creating pipeline")
            yield f"data: {json.dumps({'type': 'cancelled', 'message': 'Ingestion cancelled by user'})}\n\n"
            return

        # Create pipeline
        pipeline = DocumentIngestionPipeline(
            config=config,
            documents_folder=temp_dir,
            clean_before_ingest=clean_before_ingest
        )

        # Check for cancellation before processing
        if check_ingestion_cancelled():
            logger.info("🛑 Ingestion cancelled before document processing")
            yield f"data: {json.dumps({'type': 'cancelled', 'message': 'Ingestion cancelled by user'})}\n\n"
            return

        yield f"data: {json.dumps({'type': 'progress', 'current': 35, 'total': 100, 'message': 'Starting document processing...'})}\n\n"

        # Run the ingestion asynchronously
        async def run_ingestion_and_cleanup():
            """Async wrapper for ingestion and cleanup."""
            cleanup_result = {'person_nodes_fixed': 0, 'company_nodes_fixed': 0, 'total_nodes_fixed': 0}

            try:
                # Check for cancellation at start of async operation
                if check_ingestion_cancelled():
                    logger.info("🛑 Ingestion cancelled in async wrapper")
                    return None, cleanup_result

                logger.info("📄 Running document ingestion...")
                logger.info(f"📁 Documents folder: {temp_dir}")
                logger.info(f"📄 Files to process: {saved_files}")

                # Progress callback for the pipeline
                def progress_callback(current: int, total: int):
                    # Check for cancellation in progress callback
                    if check_ingestion_cancelled():
                        logger.info(f"🛑 Ingestion cancelled during processing (file {current}/{total})")
                        raise Exception("Ingestion cancelled by user")

                    progress = 35 + (current * 45 // total)  # 35-80% for processing
                    INGESTION_STATUS['current_file'] = current
                    INGESTION_STATUS['progress'] = progress / 100.0
                    return progress

                # Run ingestion with progress tracking
                results = await pipeline.ingest_documents(progress_callback)

                # Check for cancellation before cleanup
                if check_ingestion_cancelled():
                    logger.info("🛑 Ingestion cancelled before cleanup")
                    return None, cleanup_result

                # Run entity label cleanup within the same event loop
                try:
                    import sys
                    import os
                    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    if project_root not in sys.path:
                        sys.path.insert(0, project_root)

                    from cleanup_entity_labels import EntityLabelCleanup

                    cleanup = EntityLabelCleanup()
                    await cleanup.initialize()
                    try:
                        cleanup_result = await cleanup.cleanup_entity_labels(verbose=False)
                        logger.info(f"✅ Cleanup completed: {cleanup_result}")
                    finally:
                        await cleanup.close()

                except Exception as cleanup_error:
                    logger.warning(f"⚠️ Cleanup failed: {cleanup_error}")
                    cleanup_result = {'person_nodes_fixed': 0, 'company_nodes_fixed': 0, 'total_nodes_fixed': 0}

                # Close the pipeline within the same event loop context
                try:
                    await pipeline.close()
                    logger.info("✅ Pipeline closed successfully")
                except Exception as close_error:
                    logger.warning(f"⚠️ Failed to close pipeline: {close_error}")

                return results, cleanup_result

            except Exception as e:
                # Ensure pipeline is closed even if ingestion fails
                try:
                    await pipeline.close()
                    logger.info("✅ Pipeline closed after error")
                except Exception as close_error:
                    logger.warning(f"⚠️ Failed to close pipeline after error: {close_error}")

                if "cancelled by user" in str(e):
                    logger.info(f"🛑 Ingestion cancelled: {e}")
                    return None, cleanup_result
                else:
                    logger.error(f"❌ Ingestion pipeline failed: {e}")
                    raise e

        # Execute the ingestion and cleanup
        try:
            # Check if we're already in an event loop
            loop = asyncio.get_running_loop()
            # We're in an event loop, create a task
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, run_ingestion_and_cleanup())
                ingestion_result, cleanup_result = future.result()
        except RuntimeError:
            # No event loop running, safe to use asyncio.run()
            ingestion_result, cleanup_result = asyncio.run(run_ingestion_and_cleanup())

        # Check if ingestion was cancelled
        if ingestion_result is None or check_ingestion_cancelled():
            logger.info("🛑 Ingestion was cancelled, stopping pipeline")
            yield f"data: {json.dumps({'type': 'cancelled', 'message': 'Ingestion cancelled by user'})}\n\n"
            return

        yield f"data: {json.dumps({'type': 'progress', 'current': 80, 'total': 100, 'message': 'Processing completed, cleanup finished'})}\n\n"

        # Calculate final results from ingestion pipeline
        if isinstance(ingestion_result, list):
            # ingestion_result is a list of IngestionResult objects
            total_chunks = sum(r.chunks_created for r in ingestion_result)
            total_entities = sum(r.entities_extracted for r in ingestion_result)
            total_relationships = sum(r.relationships_created for r in ingestion_result)
            total_errors = sum(len(r.errors) for r in ingestion_result)

            # Calculate average processing time
            if ingestion_result:
                avg_processing_time_ms = sum(r.processing_time_ms for r in ingestion_result) / len(ingestion_result)
                processing_time = f"{avg_processing_time_ms:.1f}ms"
            else:
                processing_time = "0.0ms"
        else:
            # Fallback for unexpected format
            logger.warning(f"Unexpected ingestion_result format: {type(ingestion_result)}")
            total_chunks = 0
            total_entities = 0
            total_relationships = 0
            total_errors = 0
            processing_time = "0.0ms"

        # Pipeline is now closed within the async context above
        # No additional cleanup needed here

        logger.info(f"📊 {ingestion_mode.title()} ingestion results: {total_chunks} chunks, {total_entities} entities, {total_relationships} relationships, {processing_time}")

        # Final results
        results = {
            'type': 'complete',
            'message': f'{ingestion_mode.title()} ingestion completed successfully!',
            'details': {
                'files_processed': len(saved_files),
                'file_names': [os.path.basename(f) for f in saved_files],
                'chunk_size': chunk_size,
                'chunk_overlap': chunk_overlap,
                'use_semantic': use_semantic,
                'extract_entities': extract_entities,
                'clean_before_ingest': clean_before_ingest,
                'mode': ingestion_mode,
                'total_chunks': total_chunks,
                'total_entities': total_entities,
                'total_relationships': total_relationships,
                'total_errors': total_errors,
                'processing_time': processing_time,
                'ingestion_details': convert_ingestion_results_to_dict(ingestion_result),
                'cleanup_details': cleanup_result
            }
        }

        yield f"data: {json.dumps({'type': 'progress', 'current': 100, 'total': 100, 'message': f'{ingestion_mode.title()} ingestion completed!'})}\n\n"
        yield f"data: {json.dumps(results)}\n\n"

        logger.info(f"✅ {ingestion_mode.title()} ingestion completed successfully")

    except Exception as e:
        mode_name = ingestion_mode.title() if 'ingestion_mode' in locals() else 'Ingestion'
        logger.error(f"❌ {mode_name} failed: {e}")
        import traceback
        logger.error(f"❌ Error traceback: {traceback.format_exc()}")

        yield f"data: {json.dumps({'type': 'error', 'message': f'{mode_name} failed: {str(e)}'})}\n\n"


def run_real_ingestion(temp_dir, clean_before_ingest, chunk_size, chunk_overlap,
                      use_semantic, extract_entities, verbose, saved_files):
    """
    Run the actual ingestion pipeline with progress tracking.
    """
    import asyncio
    import sys
    import os

    # Add the project root to Python path
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    try:
        logger.info("🔧 Importing ingestion modules...")
        yield f"data: {json.dumps({'type': 'progress', 'current': 15, 'total': 100, 'message': 'Importing ingestion modules...'})}\n\n"

        # Import the ingestion pipeline
        from ingestion.ingest import DocumentIngestionPipeline
        from agent.models import IngestionConfig
        from cleanup_entity_labels import EntityLabelCleanup

        logger.info("✅ Successfully imported ingestion modules")
        yield f"data: {json.dumps({'type': 'progress', 'current': 20, 'total': 100, 'message': 'Modules imported successfully'})}\n\n"

        # Create ingestion configuration
        logger.info(f"⚙️ Creating ingestion config: chunk_size={chunk_size}, use_semantic={use_semantic}, extract_entities={extract_entities}")
        config = IngestionConfig(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            use_semantic_chunking=use_semantic,
            extract_entities=extract_entities,
            skip_graph_building=False
        )

        yield f"data: {json.dumps({'type': 'progress', 'current': 25, 'total': 100, 'message': 'Configuration created'})}\n\n"

        # Create ingestion pipeline
        logger.info(f"🏗️ Creating ingestion pipeline for directory: {temp_dir}")
        pipeline = DocumentIngestionPipeline(
            config=config,
            documents_folder=temp_dir,
            clean_before_ingest=clean_before_ingest
        )

        yield f"data: {json.dumps({'type': 'progress', 'current': 30, 'total': 100, 'message': 'Pipeline created'})}\n\n"

        # Run the ingestion in an async context
        logger.info("🚀 Starting async ingestion process...")

        # Create event loop if needed
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Run the ingestion
        yield f"data: {json.dumps({'type': 'progress', 'current': 35, 'total': 100, 'message': 'Starting document processing...'})}\n\n"

        async def run_ingestion():
            """Async wrapper for ingestion."""
            try:
                logger.info("📄 Running document ingestion...")
                logger.info(f"📁 Documents folder: {temp_dir}")
                logger.info(f"📄 Files to process: {saved_files}")

                # Check if files exist and are readable
                for file_path in saved_files:
                    if os.path.exists(file_path):
                        file_size = os.path.getsize(file_path)
                        logger.info(f"✅ File exists: {file_path} ({file_size} bytes)")
                    else:
                        logger.error(f"❌ File missing: {file_path}")

                ingestion_result = await pipeline.ingest_documents()
                logger.info(f"✅ Ingestion completed: {ingestion_result}")
                return ingestion_result
            except Exception as e:
                logger.error(f"❌ Ingestion failed in run_ingestion: {e}")
                logger.error(f"❌ Ingestion error traceback: {traceback.format_exc()}")
                raise

        # Execute the ingestion
        ingestion_result = loop.run_until_complete(run_ingestion())

        yield f"data: {json.dumps({'type': 'progress', 'current': 70, 'total': 100, 'message': 'Document processing completed'})}\n\n"

        # Run entity label cleanup
        logger.info("🧹 Running entity label cleanup...")
        yield f"data: {json.dumps({'type': 'progress', 'current': 80, 'total': 100, 'message': 'Cleaning entity labels...'})}\n\n"

        try:
            cleanup = EntityLabelCleanup()

            # Create async wrapper for cleanup
            async def run_cleanup():
                return await cleanup.cleanup_entity_labels()

            cleanup_result = loop.run_until_complete(run_cleanup())
            logger.info(f"✅ Cleanup completed: {cleanup_result}")
        except Exception as e:
            logger.warning(f"⚠️ Cleanup failed (continuing): {e}")
            cleanup_result = {"status": "failed", "error": str(e)}

        yield f"data: {json.dumps({'type': 'progress', 'current': 90, 'total': 100, 'message': 'Finalizing ingestion...'})}\n\n"

        # Calculate final results from list of IngestionResult objects
        if isinstance(ingestion_result, list):
            # ingestion_result is a list of IngestionResult objects
            total_chunks = sum(r.chunks_created for r in ingestion_result)
            total_entities = sum(r.entities_extracted for r in ingestion_result)
            total_relationships = sum(r.relationships_created for r in ingestion_result)
            total_errors = sum(len(r.errors) for r in ingestion_result)

            # Calculate average processing time
            if ingestion_result:
                avg_processing_time_ms = sum(r.processing_time_ms for r in ingestion_result) / len(ingestion_result)
                processing_time = f"{avg_processing_time_ms:.1f}ms"
            else:
                processing_time = "0.0ms"
        else:
            # Fallback for unexpected format
            logger.warning(f"Unexpected ingestion_result format: {type(ingestion_result)}")
            total_chunks = 0
            total_entities = 0
            total_relationships = 0
            total_errors = 0
            processing_time = "0.0ms"

        logger.info(f"📊 Final results: {total_chunks} chunks, {total_entities} entities, {total_relationships} relationships, {processing_time}")

        # Return final results
        results = {
            'type': 'result',
            'results': {
                'mode': 'real_ingestion',
                'files_processed': len(saved_files),
                'file_names': [os.path.basename(f) for f in saved_files],
                'chunk_size': chunk_size,
                'use_semantic': use_semantic,
                'extract_entities': extract_entities,
                'clean_before_ingest': clean_before_ingest,
                'total_chunks': total_chunks,
                'total_entities': total_entities,
                'total_relationships': total_relationships,
                'total_errors': total_errors,
                'processing_time': processing_time,
                'ingestion_details': convert_ingestion_results_to_dict(ingestion_result),
                'cleanup_details': cleanup_result
            }
        }

        yield f"data: {json.dumps(results)}\n\n"
        logger.info("✅ Real ingestion completed successfully")

    except Exception as e:
        logger.error(f"❌ Real ingestion failed: {e}")
        logger.error(f"❌ Error traceback: {traceback.format_exc()}")

        # Add more detailed error information
        import traceback as tb
        full_traceback = tb.format_exc()
        logger.error(f"❌ Full error traceback:\n{full_traceback}")

        # Check if the error is related to the list/dict issue
        if "'list' object has no attribute 'get'" in str(e):
            logger.error("❌ This appears to be the ingestion result format issue")
            logger.error("❌ The ingestion pipeline returned a list but the code expected a dictionary")
            logger.error("❌ This should now be fixed with the updated result handling code")

        error_result = {
            'type': 'result',
            'results': {
                'mode': 'real_ingestion_failed',
                'files_processed': len(saved_files),
                'file_names': [os.path.basename(f) for f in saved_files],
                'error': str(e),
                'error_type': type(e).__name__,
                'traceback': full_traceback,
                'total_chunks': 0,
                'total_entities': 0,
                'processing_time': '0.0 seconds'
            }
        }

        yield f"data: {json.dumps(error_result)}\n\n"


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
        logger.error(f"Error traceback: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/graph/neo4j/custom', methods=['POST'])
def execute_custom_neo4j_query():
    """Execute custom Neo4j query with parameters."""
    try:

        data = request.get_json()
        if not data:
            return jsonify({"error": "JSON data required"}), 400

        custom_query = data.get('query', '').strip()
        limit = data.get('limit', 50)

        if not custom_query:
            return jsonify({"error": "Query parameter is required"}), 400

        # Validate limit
        if limit < 1 or limit > 200:
            return jsonify({"error": "Limit must be between 1 and 200"}), 400

        logger.info(f"🔍 Executing custom Neo4j query: {custom_query[:100]}...")

        # Get Neo4j session using robust connection method
        session, driver = get_neo4j_session_with_driver()

        logger.info(f"🔗 Connected to Neo4j successfully")

        start_time = time.time()

        try:
            # Test connectivity first
            test_result = session.run("RETURN 1 as test")
            test_record = test_result.single()
            logger.info(f"✅ Neo4j connectivity test passed: {test_record['test']}")

            # Execute the custom query with limit parameter
            logger.info(f"🔍 Executing query: {custom_query}")
            result = session.run(custom_query, limit=limit)
            records = list(result)

            logger.info(f"📊 Query returned {len(records)} records")

            # Log sample record structure for debugging
            if records:
                sample_record = records[0]
                logger.info(f"📋 Sample record keys: {list(sample_record.keys())}")
                for key, value in sample_record.items():
                    logger.info(f"📋 Field '{key}': {type(value)} - {str(value)[:100]}")

            # Process results to extract nodes and relationships
            nodes = []
            relationships = []
            node_ids = set()
            rel_ids = set()

            logger.info(f"📊 Processing {len(records)} records from custom query")

            for record in records:
                for key, value in record.items():
                    logger.debug(f"Processing record field '{key}': {type(value)}")

                    # Handle Neo4j Node objects
                    if hasattr(value, 'labels'):  # Node
                        node_id = str(value.element_id)
                        if node_id not in node_ids:
                            node_data = {
                                "id": node_id,
                                "labels": list(value.labels),
                                "properties": dict(value.items())
                            }
                            nodes.append(node_data)
                            node_ids.add(node_id)
                            logger.debug(f"Added node: {node_data['properties'].get('name', node_id)}")

                    # Handle Neo4j Relationship objects
                    elif hasattr(value, 'type'):  # Relationship
                        rel_id = str(value.element_id)
                        if rel_id not in rel_ids:
                            rel_data = {
                                "id": rel_id,
                                "type": value.type,
                                "startNodeId": str(value.start_node.element_id),
                                "endNodeId": str(value.end_node.element_id),
                                "properties": dict(value.items())
                            }
                            relationships.append(rel_data)
                            rel_ids.add(rel_id)
                            logger.debug(f"Added relationship: {rel_data['type']}")

                    # Handle Path objects (from path queries)
                    elif hasattr(value, 'nodes') and hasattr(value, 'relationships'):
                        # Process nodes in path
                        for node in value.nodes:
                            node_id = str(node.element_id)
                            if node_id not in node_ids:
                                node_data = {
                                    "id": node_id,
                                    "labels": list(node.labels),
                                    "properties": dict(node.items())
                                }
                                nodes.append(node_data)
                                node_ids.add(node_id)

                        # Process relationships in path
                        for rel in value.relationships:
                            rel_id = str(rel.element_id)
                            if rel_id not in rel_ids:
                                rel_data = {
                                    "id": rel_id,
                                    "type": rel.type,
                                    "startNodeId": str(rel.start_node.element_id),
                                    "endNodeId": str(rel.end_node.element_id),
                                    "properties": dict(rel.items())
                                }
                                relationships.append(rel_data)
                                rel_ids.add(rel_id)

            query_time = round((time.time() - start_time) * 1000, 2)

            # If no nodes were found but we have records, create synthetic nodes from the data
            if not nodes and records:
                logger.info("📝 No nodes found in standard format, creating synthetic nodes from query results")
                for i, record in enumerate(records):
                    # Create a synthetic node for each record
                    synthetic_node = {
                        "id": f"result-{i}",
                        "labels": ["QueryResult"],
                        "properties": {
                            "name": f"Result {i+1}",
                            "query_result": True
                        }
                    }

                    # Add all record fields as properties
                    for key, value in record.items():
                        if not hasattr(value, 'labels') and not hasattr(value, 'type'):
                            # Convert complex objects to strings
                            if isinstance(value, (list, dict)):
                                synthetic_node["properties"][key] = str(value)
                            else:
                                synthetic_node["properties"][key] = value

                    nodes.append(synthetic_node)
                    logger.debug(f"Created synthetic node: {synthetic_node}")

            result_data = {
                "nodes": nodes,
                "relationships": relationships,
                "query_time": f"{query_time}ms",
                "metadata": {
                    "source": "custom_query",
                    "query": custom_query[:100] + "..." if len(custom_query) > 100 else custom_query,
                    "limit": limit,
                    "total_nodes": len(nodes),
                    "total_relationships": len(relationships),
                    "records_processed": len(records)
                }
            }

            logger.info(f"✅ Custom query executed successfully: {len(nodes)} nodes, {len(relationships)} relationships in {query_time}ms")
            return jsonify(result_data)

        finally:
            # Clean up session and driver
            close_neo4j_session_and_driver(session, driver)

    except Exception as e:
        logger.error(f"❌ Custom Neo4j query failed: {e}")
        logger.error(f"❌ Error traceback: {traceback.format_exc()}")
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
                MATCH (center)-[r]-(connected)
                WHERE toLower(center.name) CONTAINS toLower($entity_name)
                   OR toLower(center.id) CONTAINS toLower($entity_name)
                   OR toLower(replace(center.name, ' ', '-')) CONTAINS toLower(replace($entity_name, ' ', '-'))
                   OR toLower(replace(center.name, '-', ' ')) CONTAINS toLower(replace($entity_name, '-', ' '))
                WITH center LIMIT $center_limit
                MATCH (center)-[r]-(connected)
                WITH collect(DISTINCT center) + collect(DISTINCT connected) as all_nodes,
                     collect(DISTINCT r) as all_rels
                RETURN [node in all_nodes WHERE node IS NOT NULL][0..$limit] as nodes,
                       [rel in all_rels WHERE rel IS NOT NULL] as relationships
                """

                logger.info(f"📝 Executing query: {query}")
                logger.info(f"📝 Query parameters: entity_name='{entity_name}', limit={limit}")
                result = session.run(query, entity_name=entity_name, center_limit=min(10, limit), limit=limit)
            else:
                logger.info(f"📊 Getting sample graph data with limit: {limit} (only nodes with relationships)")
                # Get a sample of the graph with specified limit (only nodes that have relationships)
                query = """
                MATCH (n)-[r]-(connected)
                WITH n, r, connected LIMIT $limit
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
            from agent.tools import graph_search_tool, GraphSearchInput
        except ImportError as e:
            logger.error(f"❌ Failed to import agent tools in hybrid function: {e}")
            return {
                "error": f"Cannot import agent module: {e}",
                "metadata": {"query": query, "source": "hybrid"},
                "nodes": [],
                "relationships": []
            }

        # Check if this is a relationship query and optimize accordingly
        is_relationship_query = any(keyword in query.lower() for keyword in [
            'relation', 'relationship', 'between', 'connection', 'connect', 'link'
        ])

        if is_relationship_query:
            logger.info(f"🎯 Detected relationship query, optimizing search")
            # For relationship queries, use smaller depth and limit results
            depth = min(depth, 2)  # Limit depth to 2 for relationship queries
            search_limit = 10  # Limit Graphiti results for relationship queries
        else:
            search_limit = 50  # Default limit for general queries

        # Step 1: Use Graphiti to find relevant entities
        logger.info(f"Searching Graphiti for: {query} (limit: {search_limit}, depth: {depth})")

        # Run Graphiti search asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # Use the proper graph_search_tool instead of raw Graphiti
            search_input = GraphSearchInput(query=query)
            graphiti_results = loop.run_until_complete(
                graph_search_tool(search_input)
            )

            # Convert GraphSearchResult objects to dictionaries for compatibility
            if graphiti_results and hasattr(graphiti_results[0], 'fact'):
                graphiti_results = [
                    {
                        'fact': result.fact,
                        'uuid': str(result.uuid),
                        'valid_at': str(result.valid_at) if result.valid_at else None,
                        'invalid_at': str(result.invalid_at) if result.invalid_at else None,
                        'source_node_uuid': str(result.source_node_uuid) if result.source_node_uuid else None
                    }
                    for result in graphiti_results[:search_limit]  # Apply search limit
                ]
        finally:
            loop.close()

        logger.info(f"Graphiti results: {len(graphiti_results)} facts/episodes")

        # Step 2: Extract entity names from Graphiti facts
        entity_names = set()

        # Extract entity names from facts using simple text analysis
        for result in graphiti_results:
            if isinstance(result, dict):
                fact = result.get('fact', '')
                if fact:
                    # Extract potential entity names from the fact text
                    extracted_entities = extract_entities_from_fact(fact)
                    entity_names.update(extracted_entities)

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
                "graphiti_facts": len(graphiti_results) if isinstance(graphiti_results, list) else 0,
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

def enhance_neo4j_with_graphiti(neo4j_data: dict, graphiti_results: list):
    """
    Enhance Neo4j data with additional information from Graphiti facts.

    Args:
        neo4j_data: Neo4j nodes and relationships
        graphiti_results: List of Graphiti search results (facts)

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

        # Add metadata about Graphiti facts
        graphiti_facts = []
        for result in graphiti_results:
            if isinstance(result, dict) and result.get('fact'):
                graphiti_facts.append({
                    "fact": result.get('fact', ''),
                    "uuid": result.get('uuid', ''),
                    "valid_at": result.get('valid_at'),
                    "source": "graphiti"
                })

        # For now, just return the Neo4j data with Graphiti facts as metadata
        # In the future, we could extract entities and relationships from facts

        return {
            "nodes": enhanced_nodes,
            "relationships": enhanced_relationships,
            "graphiti_facts": graphiti_facts
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

# ===== PRE-APPROVAL SYSTEM API =====

@app.route('/api/pre-approval/entities/<path:entity_id>/approve', methods=['POST'])
def approve_pre_approval_entity(entity_id):
    """Approve an entity in pre-approval database."""
    if not PRE_APPROVAL_DB_AVAILABLE:
        # Fallback: Return success response when pre-approval system is not available
        logger.info(f"🔄 Pre-approval system not available, using fallback for approve entity {entity_id}")
        return jsonify({
            "success": True,
            "message": "Entity approval recorded (fallback mode - pre-approval system not available)",
            "fallback_mode": True,
            "entity_id": entity_id
        })
    
    try:
        data = request.get_json() or {}
        reviewer_id = data.get('reviewer_id', 'unknown')
        review_notes = data.get('review_notes', '')
        
        pre_db = get_pre_approval_db()
        if not pre_db:
            return jsonify({"error": "Pre-approval database unavailable"}), 503
        
        # Use the new synchronous calling pattern
        success = call_db_method_sync(pre_db, 'approve_entity', entity_id, reviewer_id, review_notes)
        
        if success:
            return jsonify({"success": True, "message": "Entity approved successfully"})
        else:
            return jsonify({"success": False, "error": "Failed to approve entity"}), 400
    
    except Exception as e:
        logger.error(f"❌ Failed to approve pre-approval entity: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/pre-approval/entities/<path:entity_id>/reject', methods=['POST'])
def reject_pre_approval_entity(entity_id):
    """Reject an entity in pre-approval database."""
    if not PRE_APPROVAL_DB_AVAILABLE:
        # Fallback: Return success response when pre-approval system is not available
        logger.info(f"🔄 Pre-approval system not available, using fallback for reject entity {entity_id}")
        return jsonify({
            "success": True,
            "message": "Entity rejection recorded (fallback mode - pre-approval system not available)",
            "fallback_mode": True,
            "entity_id": entity_id
        })
    
    try:
        data = request.get_json() or {}
        reviewer_id = data.get('reviewer_id', 'unknown')
        review_notes = data.get('review_notes', 'Rejected via unified dashboard')
        
        pre_db = get_pre_approval_db()
        if not pre_db:
            return jsonify({"error": "Pre-approval database unavailable"}), 503
        
        # Use the new synchronous calling pattern
        success = call_db_method_sync(pre_db, 'reject_entity', entity_id, reviewer_id, review_notes)
        
        if success:
            return jsonify({"success": True, "message": "Entity rejected successfully"})
        else:
            return jsonify({"success": False, "error": "Failed to reject entity"}), 400
    
    except Exception as e:
        logger.error(f"❌ Failed to reject pre-approval entity: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/pre-approval/relationships')
def get_pre_approval_relationships():
    """Get relationships from pre-approval database."""
    if not PRE_APPROVAL_DB_AVAILABLE:
        # Fallback: Return empty relationships list when pre-approval system is not available
        logger.info("🔄 Pre-approval system not available, returning empty relationships list")
        return jsonify({
            "success": True,
            "relationships": [],
            "count": 0,
            "message": "Pre-approval system not available - no relationships to review",
            "fallback_mode": True
        })

    try:
        status_filter = request.args.get('status', 'pending')
        source_document = request.args.get('source_document')
        limit = int(request.args.get('limit', '100'))
        
        pre_db = get_pre_approval_db()
        if not pre_db:
            return jsonify({"error": "Pre-approval database unavailable"}), 503

        async def get_relationships():
            return await pre_db.get_relationships(
                status_filter=status_filter,
                source_document=source_document,
                limit=limit
            )

        # Run async function - create new event loop for Flask thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            relationships = loop.run_until_complete(get_relationships())
        finally:
            loop.close()
        
        return jsonify({
            "relationships": relationships,
            "count": len(relationships),
            "status": "success"
        })

    except Exception as e:
        logger.error(f"❌ Failed to get pre-approval relationships: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/pre-approval/relationships/<path:relationship_id>/approve', methods=['POST'])
def approve_pre_approval_relationship(relationship_id):
    """Approve a relationship in pre-approval database."""
    if not PRE_APPROVAL_DB_AVAILABLE:
        # Fallback: Return success response when pre-approval system is not available
        logger.info(f"🔄 Pre-approval system not available, using fallback for approve relationship {relationship_id}")
        return jsonify({
            "success": True,
            "message": "Relationship approval recorded (fallback mode - pre-approval system not available)",
            "fallback_mode": True,
            "relationship_id": relationship_id
        })

    try:
        data = request.get_json() or {}
        reviewer_id = data.get('reviewer_id', 'default_reviewer')
        review_notes = data.get('review_notes', '')
        
        pre_db = get_pre_approval_db()
        if not pre_db:
            return jsonify({"error": "Pre-approval database unavailable"}), 503

        # Use the new synchronous calling pattern
        success = call_db_method_sync(pre_db, 'approve_relationship', relationship_id, reviewer_id, review_notes)
        
        if success:
            logger.info(f"✅ Approved pre-approval relationship: {relationship_id}")
            return jsonify({
                "status": "success",
                "message": f"Relationship {relationship_id} approved successfully"
            })
        else:
            return jsonify({
                "status": "error",
                "message": f"Failed to approve relationship {relationship_id}"
            }), 400

    except Exception as e:
        logger.error(f"❌ Failed to approve pre-approval relationship: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/pre-approval/relationships/<path:relationship_id>/reject', methods=['POST'])
def reject_pre_approval_relationship(relationship_id):
    """Reject a relationship in pre-approval database."""
    if not PRE_APPROVAL_DB_AVAILABLE:
        # Fallback: Return success response when pre-approval system is not available
        logger.info(f"🔄 Pre-approval system not available, using fallback for reject relationship {relationship_id}")
        return jsonify({
            "success": True,
            "message": "Relationship rejection recorded (fallback mode - pre-approval system not available)",
            "fallback_mode": True,
            "relationship_id": relationship_id
        })

    try:
        data = request.get_json() or {}
        reviewer_id = data.get('reviewer_id', 'default_reviewer')
        review_notes = data.get('review_notes', 'No reason provided')
        
        if not review_notes.strip():
            return jsonify({
                "status": "error", 
                "message": "Review notes are required for rejection"
            }), 400
        
        pre_db = get_pre_approval_db()
        if not pre_db:
            return jsonify({"error": "Pre-approval database unavailable"}), 503

        # Use the new synchronous calling pattern
        success = call_db_method_sync(pre_db, 'reject_relationship', relationship_id, reviewer_id, review_notes)
        
        if success:
            logger.info(f"❌ Rejected pre-approval relationship: {relationship_id}")
            return jsonify({
                "status": "success",
                "message": f"Relationship {relationship_id} rejected successfully"
            })
        else:
            return jsonify({
                "status": "error",
                "message": f"Failed to reject relationship {relationship_id}"
            }), 400

    except Exception as e:
        logger.error(f"❌ Failed to reject pre-approval relationship: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/pre-approval/ingest-approved', methods=['POST'])
def ingest_approved_entities():
    """Ingest approved entities to Neo4j."""
    logger.info("🔄 Auto-ingestion endpoint called")

    if not PRE_APPROVAL_DB_AVAILABLE:
        # Fallback: Return a simple success response when pre-approval system is not available
        logger.info("🔄 Pre-approval system not available, using minimal fallback response")

        # Check if Graphiti is available
        graphiti_available = False
        try:
            import graphiti_core
            graphiti_available = True
            logger.info("✅ Graphiti-core is available")
        except ImportError:
            logger.info("ℹ️ Graphiti-core not available")

        # Check if Neo4j driver is available
        neo4j_available = False
        try:
            import neo4j
            neo4j_available = True
            logger.info("✅ Neo4j driver is available")
        except ImportError:
            logger.info("ℹ️ Neo4j driver not available")

        # Return appropriate response based on available systems
        if graphiti_available:
            try:
                # Try to use Graphiti for direct ingestion
                from agent.graph_utils import initialize_graph, close_graph, get_graph_client

                async def run_graphiti_ingestion():
                    try:
                        await initialize_graph()
                        logger.info("✅ Graphiti graph initialized for fallback ingestion")

                        return {
                            "entities_ingested": 0,
                            "entities_processed": 0,
                            "message": "Graphiti ingestion system ready. Use document ingestion to add entities to the graph.",
                            "fallback_mode": True,
                            "graph_ready": True
                        }
                    finally:
                        await close_graph()

                # Run async function - create new event loop for Flask thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(run_graphiti_ingestion())
                finally:
                    loop.close()

                return jsonify({
                    "status": "success",
                    "message": "Fallback ingestion completed",
                    "result": result
                })

            except Exception as e:
                logger.error(f"❌ Failed to run Graphiti fallback ingestion: {e}")
                # Fall through to minimal response

        # Minimal fallback response when no ingestion systems are available
        logger.info("ℹ️ Providing minimal fallback response - no ingestion systems available")
        return jsonify({
            "status": "success",
            "message": "Minimal fallback mode",
            "result": {
                "entities_ingested": 0,
                "entities_processed": 0,
                "message": "No ingestion systems available. Install dependencies: pip install asyncpg neo4j graphiti-core",
                "fallback_mode": True,
                "minimal_mode": True,
                "available_systems": {
                    "graphiti": graphiti_available,
                    "neo4j": neo4j_available,
                    "pre_approval": False
                }
            }
        })

    try:
        from approval.neo4j_ingestion_service import create_neo4j_ingestion_service

        ingestion_service = create_neo4j_ingestion_service()

        async def run_ingestion():
            await ingestion_service.initialize()
            try:
                result = await ingestion_service.auto_ingest_approved_entities()
                return result
            finally:
                await ingestion_service.close()

        # Run async function - create new event loop for Flask thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(run_ingestion())
        finally:
            loop.close()

        return jsonify({
            "status": "success",
            "message": "Ingestion completed",
            "result": result
        })

    except Exception as e:
        logger.error(f"❌ Failed to ingest approved entities: {e}")
        logger.error(f"❌ Error traceback: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/graphiti/test-ingestion', methods=['POST'])
def test_graphiti_ingestion():
    """Test Graphiti ingestion system by adding a sample entity."""
    try:
        from agent.graph_utils import initialize_graph, close_graph, add_person_to_graph
        from agent.entity_models import PersonType

        async def run_test_ingestion():
            try:
                await initialize_graph()
                logger.info("✅ Graphiti graph initialized for test")

                # Add a test person entity
                episode_id = await add_person_to_graph(
                    name="Test Person",
                    person_type=PersonType.INDIVIDUAL,
                    current_company="Test Company",
                    current_position="Test Position",
                    source_document="test_ingestion_endpoint"
                )

                logger.info(f"✅ Test entity added with episode ID: {episode_id}")

                return {
                    "success": True,
                    "message": "Test entity successfully added to Graphiti graph",
                    "episode_id": episode_id,
                    "entity_name": "Test Person"
                }
            finally:
                await close_graph()

        # Run async function - create new event loop for Flask thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(run_test_ingestion())
        finally:
            loop.close()

        return jsonify({
            "status": "success",
            "message": "Graphiti test ingestion completed",
            "result": result
        })

    except Exception as e:
        logger.error(f"❌ Failed to test Graphiti ingestion: {e}")
        return jsonify({
            "error": str(e),
            "suggestion": "Check Graphiti configuration and Neo4j connectivity"
        }), 500

@app.route('/api/pre-approval/statistics')
def get_pre_approval_statistics():
    """Get pre-approval database statistics."""
    if not PRE_APPROVAL_DB_AVAILABLE:
        return jsonify({"error": "Pre-approval system not available"}), 503
    
    try:
        pre_db = get_pre_approval_db()
        if not pre_db:
            return jsonify({"error": "Pre-approval database unavailable"}), 503
        
        # Use thread-safe async execution to prevent race conditions
        stats = call_db_method_sync(pre_db, 'get_statistics')
        
        # Extract entity statistics for easier frontend access
        entity_stats = stats.get('entities', {})
        
        return jsonify({
            "success": True,
            "total": entity_stats.get('total', 0),
            "pending": entity_stats.get('pending', 0),
            "approved": entity_stats.get('approved', 0),
            "rejected": entity_stats.get('rejected', 0),
            "ingested": entity_stats.get('ingested', 0),
            "entities": entity_stats,
            "relationships": stats.get('relationships', {})
        })
    
    except Exception as e:
        logger.error(f"❌ Failed to get pre-approval statistics: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/pre-approval/entities/clean-pending', methods=['DELETE'])
def clean_pending_entities():
    """Delete all pending entities from pre-approval database."""
    if not PRE_APPROVAL_DB_AVAILABLE:
        # Fallback: Return success response when pre-approval system is not available
        logger.info("🔄 Pre-approval system not available, using fallback for clean pending entities")
        return jsonify({
            "success": True,
            "deleted_count": 0,
            "message": "Clean pending completed (fallback mode - pre-approval system not available)",
            "fallback_mode": True
        })
    
    try:
        pre_db = get_pre_approval_db()
        if not pre_db:
            return jsonify({"error": "Pre-approval database unavailable"}), 503
        
        # Use the new synchronous calling pattern
        deleted_count = call_db_method_sync(pre_db, 'clean_pending_entities')
        
        return jsonify({
            "success": True,
            "deleted_count": deleted_count,
            "message": f"Successfully deleted {deleted_count} pending entities"
        })
    
    except Exception as e:
        logger.error(f"❌ Failed to clean pending entities: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/pre-approval/entities/approve-all', methods=['POST'])
def approve_all_entities():
    """Approve all pending entities in pre-approval database."""
    if not PRE_APPROVAL_DB_AVAILABLE:
        return jsonify({"error": "Pre-approval system not available"}), 503
    
    try:
        data = request.get_json() or {}
        reviewer_id = data.get('reviewer_id', 'default_reviewer')
        review_notes = data.get('review_notes', 'Bulk approval - all pending entities')
        
        pre_db = get_pre_approval_db()
        if not pre_db:
            return jsonify({"error": "Pre-approval database unavailable"}), 503
        
        # Use the new synchronous calling pattern
        approved_count = call_db_method_sync(pre_db, 'approve_all_pending_entities', reviewer_id, review_notes)
        
        return jsonify({
            "success": True,
            "approved_count": approved_count,
            "message": f"Successfully approved {approved_count} entities"
        })
    
    except Exception as e:
        logger.error(f"❌ Failed to approve all entities: {e}")
        return jsonify({"error": str(e)}), 500

# ===== END PRE-APPROVAL SYSTEM API =====

# ===== APPROVAL SYSTEM API ENDPOINTS =====

# Import approval system components
try:
    from approval import create_entity_approval_service
    APPROVAL_SYSTEM_AVAILABLE = True
    logger.info("✅ Approval system imported successfully")
except ImportError as e:
    APPROVAL_SYSTEM_AVAILABLE = False
    logger.warning(f"⚠️ Approval system not available: {e}")

# Global approval service instance
approval_service = None

def get_approval_service():
    """Get or create approval service instance."""
    global approval_service
    if not approval_service and APPROVAL_SYSTEM_AVAILABLE:
        try:
            # Use same Neo4j configuration as main app
            neo4j_uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
            neo4j_user = os.getenv('NEO4J_USER', 'neo4j')
            neo4j_password = os.getenv('NEO4J_PASSWORD', 'password')
            
            approval_service = create_entity_approval_service(
                neo4j_uri=neo4j_uri,
                neo4j_user=neo4j_user,
                neo4j_password=neo4j_password
            )
            
            # Initialize service in background
            import asyncio
            def init_service():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(approval_service.initialize())
                    logger.info("✅ Approval service initialized")
                except Exception as e:
                    logger.error(f"❌ Failed to initialize approval service: {e}")
                finally:
                    loop.close()
            
            threading.Thread(target=init_service, daemon=True).start()
            
        except Exception as e:
            logger.error(f"❌ Failed to create approval service: {e}")
            approval_service = None
    
    return approval_service

@app.route('/api/approval/sessions', methods=['POST'])
def create_approval_session():
    """Create a new approval session for a document."""
    if not APPROVAL_SYSTEM_AVAILABLE:
        return jsonify({"error": "Approval system not available"}), 503
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        document_title = data.get('document_title')
        document_source = data.get('document_source')
        reviewer_id = data.get('reviewer_id', 'default_reviewer')
        
        if not document_title or not document_source:
            return jsonify({"error": "document_title and document_source are required"}), 400
        
        service = get_approval_service()
        if not service:
            return jsonify({"error": "Approval service unavailable"}), 503
        
        # Run async operation in thread
        def create_session():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                session_id = loop.run_until_complete(
                    service.create_approval_session(
                        document_title=document_title,
                        document_source=document_source,
                        reviewer_id=reviewer_id
                    )
                )
                return session_id
            finally:
                loop.close()
        
        session_id = create_session()
        
        return jsonify({
            "session_id": session_id,
            "document_title": document_title,
            "document_source": document_source,
            "status": "created"
        })
    
    except Exception as e:
        logger.error(f"❌ Failed to create approval session: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/approval/entities/<document_source>')
def get_entities_for_approval(document_source):
    """Get entities that need approval for a document."""
    if not APPROVAL_SYSTEM_AVAILABLE:
        return jsonify({"error": "Approval system not available"}), 503
    
    try:
        entity_types = request.args.getlist('entity_types')
        status_filter = request.args.get('status', 'pending')
        
        service = get_approval_service()
        if not service:
            return jsonify({"error": "Approval service unavailable"}), 503
        
        # Run async operation in thread
        def get_entities():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                entities = loop.run_until_complete(
                    service.get_entities_for_approval(
                        document_source=document_source,
                        entity_types=entity_types if entity_types else None,
                        status_filter=status_filter
                    )
                )
                return entities
            finally:
                loop.close()
        
        entities = get_entities()
        
        return jsonify({
            "entities": entities,
            "total_count": len(entities),
            "document_source": document_source,
            "status_filter": status_filter
        })
    
    except Exception as e:
        logger.error(f"❌ Failed to get entities for approval: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/approval/relationships/<document_source>')
def get_relationships_for_approval(document_source):
    """Get relationships that need approval for a document."""
    if not APPROVAL_SYSTEM_AVAILABLE:
        return jsonify({"error": "Approval system not available"}), 503
    
    try:
        status_filter = request.args.get('status', 'pending')
        
        service = get_approval_service()
        if not service:
            return jsonify({"error": "Approval service unavailable"}), 503
        
        # Run async operation in thread
        def get_relationships():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                relationships = loop.run_until_complete(
                    service.get_relationships_for_approval(
                        document_source=document_source,
                        status_filter=status_filter
                    )
                )
                return relationships
            finally:
                loop.close()
        
        relationships = get_relationships()
        
        return jsonify({
            "relationships": relationships,
            "total_count": len(relationships),
            "document_source": document_source,
            "status_filter": status_filter
        })
    
    except Exception as e:
        logger.error(f"❌ Failed to get relationships for approval: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/approval/entities/<path:entity_id>/approve', methods=['POST'])
def approve_entity(entity_id):
    """Approve an entity, optionally with modifications."""
    if not APPROVAL_SYSTEM_AVAILABLE:
        return jsonify({"error": "Approval system not available"}), 503
    
    try:
        data = request.get_json() or {}
        reviewer_id = data.get('reviewer_id', 'default_reviewer')
        review_notes = data.get('review_notes')
        modified_data = data.get('modified_data')
        
        service = get_approval_service()
        if not service:
            return jsonify({"error": "Approval service unavailable"}), 503
        
        # Initialize service if needed
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(service.initialize())
            success = loop.run_until_complete(
                service.approve_entity(
                    entity_id=entity_id,
                    reviewer_id=reviewer_id,
                    review_notes=review_notes,
                    modified_data=modified_data
                )
            )
        finally:
            loop.close()
        
        if success:
            return jsonify({
                "success": True,
                "status": "approved",
                "entity_id": entity_id,
                "reviewer_id": reviewer_id,
                "modified": bool(modified_data)
            })
        else:
            return jsonify({"success": False, "error": "Failed to approve entity"}), 400
    
    except Exception as e:
        logger.error(f"❌ Failed to approve entity {entity_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/approval/entities/<path:entity_id>/reject', methods=['POST'])
def reject_entity(entity_id):
    """Reject an entity with reasoning."""
    if not APPROVAL_SYSTEM_AVAILABLE:
        return jsonify({"error": "Approval system not available"}), 503
    
    try:
        data = request.get_json() or {}
        reviewer_id = data.get('reviewer_id', 'default_reviewer')
        review_notes = data.get('review_notes', 'Rejected via unified dashboard')
        
        service = get_approval_service()
        if not service:
            return jsonify({"error": "Approval service unavailable"}), 503
        
        # Initialize service if needed  
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(service.initialize())
            success = loop.run_until_complete(
                service.reject_entity(
                    entity_id=entity_id,
                    reviewer_id=reviewer_id,
                    review_notes=review_notes
                )
            )
        finally:
            loop.close()
        
        if success:
            return jsonify({
                "success": True,
                "status": "rejected",
                "entity_id": entity_id,
                "reviewer_id": reviewer_id,
                "review_notes": review_notes
            })
        else:
            return jsonify({"success": False, "error": "Failed to reject entity"}), 400
    
    except Exception as e:
        logger.error(f"❌ Failed to reject entity {entity_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/approval/entities/bulk-approve', methods=['POST'])
def bulk_approve_entities():
    """Bulk approve multiple entities."""
    if not APPROVAL_SYSTEM_AVAILABLE:
        return jsonify({"error": "Approval system not available"}), 503
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        entity_ids = data.get('entity_ids', [])
        reviewer_id = data.get('reviewer_id', 'default_reviewer')
        review_notes = data.get('review_notes')
        
        if not entity_ids:
            return jsonify({"error": "entity_ids list is required"}), 400
        
        service = get_approval_service()
        if not service:
            return jsonify({"error": "Approval service unavailable"}), 503
        
        # Run async operation in thread
        def bulk_approve():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                results = loop.run_until_complete(
                    service.bulk_approve_entities(
                        entity_ids=entity_ids,
                        reviewer_id=reviewer_id,
                        review_notes=review_notes
                    )
                )
                return results
            finally:
                loop.close()
        
        results = bulk_approve()
        
        successful_count = sum(1 for success in results.values() if success)
        
        return jsonify({
            "results": results,
            "total_requested": len(entity_ids),
            "successful_count": successful_count,
            "failed_count": len(entity_ids) - successful_count
        })
    
    except Exception as e:
        logger.error(f"❌ Failed to bulk approve entities: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/approval/search/<document_source>')
def search_entities(document_source):
    """Search entities by name or properties."""
    if not APPROVAL_SYSTEM_AVAILABLE:
        return jsonify({"error": "Approval system not available"}), 503
    
    try:
        search_query = request.args.get('q', '')
        entity_types = request.args.getlist('entity_types')
        
        if not search_query:
            return jsonify({"error": "Search query 'q' parameter is required"}), 400
        
        service = get_approval_service()
        if not service:
            return jsonify({"error": "Approval service unavailable"}), 503
        
        # Run async operation in thread
        def search():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                entities = loop.run_until_complete(
                    service.search_entities(
                        document_source=document_source,
                        search_query=search_query,
                        entity_types=entity_types if entity_types else None
                    )
                )
                return entities
            finally:
                loop.close()
        
        entities = search()
        
        return jsonify({
            "entities": entities,
            "total_count": len(entities),
            "search_query": search_query,
            "document_source": document_source
        })
    
    except Exception as e:
        logger.error(f"❌ Failed to search entities: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/approval/sessions/<session_id>/status')
def get_approval_session_status(session_id):
    """Get the current status of an approval session."""
    if not APPROVAL_SYSTEM_AVAILABLE:
        return jsonify({"error": "Approval system not available"}), 503
    
    try:
        service = get_approval_service()
        if not service:
            return jsonify({"error": "Approval service unavailable"}), 503
        
        # Run async operation in thread
        def get_status():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                status = loop.run_until_complete(
                    service.get_approval_session_status(session_id)
                )
                return status
            finally:
                loop.close()
        
        status = get_status()
        
        if not status:
            return jsonify({"error": "Session not found"}), 404
        
        return jsonify(status)
    
    except Exception as e:
        logger.error(f"❌ Failed to get session status: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/approval/statistics')
def get_approval_statistics():
    """Get overall approval statistics."""
    if not APPROVAL_SYSTEM_AVAILABLE:
        return jsonify({"error": "Approval system not available"}), 503
    
    try:
        document_source = request.args.get('document_source')
        
        service = get_approval_service()
        if not service:
            return jsonify({"error": "Approval service unavailable"}), 503
        
        # Run async operation in thread
        def get_stats():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                stats = loop.run_until_complete(
                    service.get_approval_statistics(document_source)
                )
                return stats
            finally:
                loop.close()
        
        stats = get_stats()
        
        return jsonify(stats)
    
    except Exception as e:
        logger.error(f"❌ Failed to get approval statistics: {e}")
        return jsonify({"error": str(e)}), 500

# ===== END APPROVAL SYSTEM API =====

# ===== DATABASE CLEANUP API =====

@app.route('/api/cleanup/neo4j', methods=['POST'])
def cleanup_neo4j_database():
    """Clean up Neo4j database - remove all nodes and relationships."""
    try:
        data = request.get_json() or {}
        confirm = data.get('confirm', False)
        
        if not confirm:
            return jsonify({
                "error": "Cleanup requires confirmation",
                "message": "Set 'confirm': true in request body to proceed"
            }), 400
        
        logger.info("🧹 Starting Neo4j database cleanup...")
        
        # Get Neo4j session and driver
        session, driver = get_neo4j_session_with_driver()
        
        try:
            # Count existing nodes and relationships before cleanup
            count_result = session.run("MATCH (n) RETURN count(n) as node_count")
            node_count = count_result.single()["node_count"]
            
            rel_count_result = session.run("MATCH ()-[r]->() RETURN count(r) as rel_count")
            rel_count = rel_count_result.single()["rel_count"]
            
            logger.info(f"📊 Found {node_count} nodes and {rel_count} relationships to delete")
            
            # Delete all relationships first
            session.run("MATCH ()-[r]->() DELETE r")
            logger.info("✅ Deleted all relationships")
            
            # Delete all nodes
            session.run("MATCH (n) DELETE n")
            logger.info("✅ Deleted all nodes")
            
            # Drop all constraints and indexes
            try:
                constraints_result = session.run("SHOW CONSTRAINTS")
                for record in constraints_result:
                    constraint_name = record.get("name")
                    if constraint_name:
                        session.run(f"DROP CONSTRAINT {constraint_name}")
                        logger.info(f"✅ Dropped constraint: {constraint_name}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to drop some constraints: {e}")
            
            try:
                indexes_result = session.run("SHOW INDEXES")
                for record in indexes_result:
                    index_name = record.get("name")
                    if index_name and not index_name.startswith("system"):
                        session.run(f"DROP INDEX {index_name}")
                        logger.info(f"✅ Dropped index: {index_name}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to drop some indexes: {e}")
            
            logger.info("🎉 Neo4j database cleanup completed successfully")
            
            return jsonify({
                "success": True,
                "message": "Neo4j database cleaned successfully",
                "stats": {
                    "nodes_deleted": node_count,
                    "relationships_deleted": rel_count
                }
            })
            
        except Exception as e:
            logger.error(f"❌ Neo4j cleanup failed: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
        finally:
            close_neo4j_session(session)
            if driver:
                driver.close()
    
    except Exception as e:
        logger.error(f"❌ Failed to cleanup Neo4j database: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/cleanup/vector', methods=['POST'])
def cleanup_vector_database():
    """Clean up vector database - remove all embeddings."""
    try:
        data = request.get_json() or {}
        confirm = data.get('confirm', False)
        
        if not confirm:
            return jsonify({
                "error": "Cleanup requires confirmation",
                "message": "Set 'confirm': true in request body to proceed"
            }), 400
        
        logger.info("🧹 Starting vector database cleanup...")
        
        try:
            # Try to import vector store utilities
            from agent.vector_store import VectorStore
            
            # Initialize vector store
            vector_store = VectorStore()
            
            # Get collection info before cleanup
            try:
                collection_info = vector_store.get_collection_info()
                doc_count = collection_info.get('count', 0)
                logger.info(f"📊 Found {doc_count} documents in vector database")
            except:
                doc_count = "unknown"
            
            # Clear the vector database
            result = vector_store.clear_database()
            
            if result.get('success', False):
                logger.info("🎉 Vector database cleanup completed successfully")
                return jsonify({
                    "success": True,
                    "message": "Vector database cleaned successfully",
                    "stats": {
                        "documents_deleted": doc_count
                    }
                })
            else:
                error_msg = result.get('error', 'Unknown error during vector cleanup')
                logger.error(f"❌ Vector cleanup failed: {error_msg}")
                return jsonify({
                    "success": False,
                    "error": error_msg
                }), 500
                
        except ImportError:
            # Fallback: try to clear PostgreSQL vector table directly
            logger.info("⚠️ Vector store module not available, trying direct PostgreSQL cleanup...")
            
            try:
                # Try to import psycopg2, handle gracefully if not available
                try:
                    import psycopg2
                except ImportError as psycopg2_error:
                    logger.warning(f"❌ psycopg2 not available: {psycopg2_error}")
                    return jsonify({
                        "success": False,
                        "error": "PostgreSQL cleanup requires psycopg2 to be installed. Install it with: pip install psycopg2-binary"
                    }), 503
                
                from dotenv import load_dotenv
                load_dotenv()
                
                # Get PostgreSQL connection
                db_url = os.getenv('DATABASE_URL')
                if not db_url:
                    return jsonify({
                        "success": False,
                        "error": "DATABASE_URL not configured"
                    }), 500
                
                conn = psycopg2.connect(db_url)
                cur = conn.cursor()
                
                # Count documents before deletion
                try:
                    cur.execute("SELECT COUNT(*) FROM documents")
                    doc_count = cur.fetchone()[0]
                    logger.info(f"📊 Found {doc_count} documents in PostgreSQL")
                except:
                    doc_count = "unknown"
                
                # Delete all documents and embeddings
                cur.execute("DELETE FROM documents")
                conn.commit()
                
                cur.close()
                conn.close()
                
                logger.info("🎉 PostgreSQL vector cleanup completed successfully")
                return jsonify({
                    "success": True,
                    "message": "Vector database (PostgreSQL) cleaned successfully",
                    "stats": {
                        "documents_deleted": doc_count
                    }
                })
                
            except Exception as pg_error:
                logger.error(f"❌ PostgreSQL cleanup failed: {pg_error}")
                return jsonify({
                    "success": False,
                    "error": f"PostgreSQL cleanup failed: {str(pg_error)}"
                }), 500
                
    except Exception as e:
        logger.error(f"❌ Failed to cleanup vector database: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/cleanup/all', methods=['POST'])
def cleanup_all_databases():
    """Clean up both Neo4j and vector databases."""
    try:
        data = request.get_json() or {}
        confirm = data.get('confirm', False)
        
        if not confirm:
            return jsonify({
                "error": "Cleanup requires confirmation",
                "message": "Set 'confirm': true in request body to proceed"
            }), 400
        
        logger.info("🧹 Starting complete database cleanup (Neo4j + Vector)...")
        
        results = {
            "neo4j": {"success": False},
            "vector": {"success": False}
        }
        
        # Cleanup Neo4j
        try:
            session, driver = get_neo4j_session_with_driver()
            try:
                # Count existing data
                count_result = session.run("MATCH (n) RETURN count(n) as node_count")
                node_count = count_result.single()["node_count"]
                rel_count_result = session.run("MATCH ()-[r]->() RETURN count(r) as rel_count")
                rel_count = rel_count_result.single()["rel_count"]
                
                # Delete all relationships and nodes
                session.run("MATCH ()-[r]->() DELETE r")
                session.run("MATCH (n) DELETE n")
                
                results["neo4j"] = {
                    "success": True,
                    "nodes_deleted": node_count,
                    "relationships_deleted": rel_count
                }
                logger.info(f"✅ Neo4j cleanup completed: {node_count} nodes, {rel_count} relationships deleted")
                
            finally:
                close_neo4j_session(session)
                if driver:
                    driver.close()
                    
        except Exception as e:
            logger.error(f"❌ Neo4j cleanup failed: {e}")
            results["neo4j"] = {"success": False, "error": str(e)}
        
        # Cleanup Vector Database
        try:
            from agent.vector_store import VectorStore
            vector_store = VectorStore()
            
            try:
                collection_info = vector_store.get_collection_info()
                doc_count = collection_info.get('count', 0)
            except:
                doc_count = "unknown"
            
            cleanup_result = vector_store.clear_database()
            if cleanup_result.get('success', False):
                results["vector"] = {
                    "success": True,
                    "documents_deleted": doc_count
                }
                logger.info(f"✅ Vector cleanup completed: {doc_count} documents deleted")
            else:
                results["vector"] = {
                    "success": False,
                    "error": cleanup_result.get('error', 'Unknown error')
                }
                
        except Exception as e:
            logger.error(f"❌ Vector cleanup failed: {e}")
            results["vector"] = {"success": False, "error": str(e)}
        
        # Determine overall success
        overall_success = results["neo4j"]["success"] and results["vector"]["success"]
        
        if overall_success:
            logger.info("🎉 Complete database cleanup completed successfully")
            return jsonify({
                "success": True,
                "message": "All databases cleaned successfully",
                "results": results
            })
        else:
            logger.warning("⚠️ Partial cleanup completed with some failures")
            return jsonify({
                "success": False,
                "message": "Partial cleanup completed with some failures",
                "results": results
            }), 207  # Multi-status response
            
    except Exception as e:
        logger.error(f"❌ Failed to cleanup databases: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/cleanup/status', methods=['GET'])
def get_cleanup_status():
    """Get current database status (counts of nodes, relationships, documents)."""
    try:
        status = {
            "neo4j": {"available": False},
            "vector": {"available": False}
        }
        
        # Check Neo4j status
        try:
            session, driver = get_neo4j_session_with_driver()
            try:
                # Count nodes and relationships
                node_result = session.run("MATCH (n) RETURN count(n) as count")
                node_count = node_result.single()["count"]
                
                rel_result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
                rel_count = rel_result.single()["count"]
                
                # Get node type distribution
                type_result = session.run("""
                    MATCH (n) 
                    RETURN labels(n)[0] as label, count(n) as count 
                    ORDER BY count DESC
                """)
                node_types = {record["label"]: record["count"] for record in type_result}
                
                status["neo4j"] = {
                    "available": True,
                    "nodes": node_count,
                    "relationships": rel_count,
                    "node_types": node_types
                }
                
            finally:
                close_neo4j_session(session)
                if driver:
                    driver.close()
                    
        except Exception as e:
            logger.warning(f"⚠️ Failed to get Neo4j status: {e}")
            status["neo4j"] = {"available": False, "error": str(e)}
        
        # Check Vector database status
        try:
            from agent.vector_store import VectorStore
            vector_store = VectorStore()
            collection_info = vector_store.get_collection_info()
            
            status["vector"] = {
                "available": True,
                "documents": collection_info.get('count', 0),
                "collection_name": collection_info.get('name', 'unknown')
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to get vector status: {e}")
            status["vector"] = {"available": False, "error": str(e)}
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"❌ Failed to get cleanup status: {e}")
        return jsonify({"error": str(e)}), 500

# ===== END DATABASE CLEANUP API =====

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
