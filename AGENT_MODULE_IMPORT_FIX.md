# Agent Module Import Fix

## Problem Identified

The web UI was failing to import the `agent` module, causing graph visualization to fail:

```
ERROR:app:Failed to fetch Neo4j graph data: No module named 'agent'
INFO:werkzeug:127.0.0.1 - - [16/Jul/2025 22:19:03] "GET /api/graph/neo4j/visualize?depth=3&entity=Man+Ieng+IM HTTP/1.1" 200 -
```

**Root Cause:**
- The web UI runs from the `web_ui/` directory
- The `agent` module is in the parent directory
- Python's import system couldn't find the `agent` module
- No proper path setup for cross-directory imports

## Solution Implemented

### **1. Fixed Python Path Setup**

#### **Added Module-Level Path Configuration**
```python
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
```

#### **Directory Structure Understanding**
```
project/
├── agent/                    # Agent module location
│   ├── graph_utils.py       # Neo4j utilities
│   └── ...
├── web_ui/                  # Web UI location
│   ├── app.py              # Flask app (imports agent)
│   └── ...
└── ...
```

**Path Resolution:**
- `web_ui/app.py` location: `/project/web_ui/app.py`
- Parent directory: `/project/`
- Agent module: `/project/agent/`

### **2. Enhanced Error Handling**

#### **Comprehensive Import Error Handling**
```python
try:
    from agent.graph_utils import get_neo4j_driver
except ImportError as e:
    logger.error(f"❌ Failed to import agent.graph_utils: {e}")
    logger.error(f"❌ Current sys.path: {sys.path}")
    logger.error(f"❌ Current working directory: {os.getcwd()}")
    logger.error(f"❌ Web UI directory: {os.path.dirname(os.path.abspath(__file__))}")
    logger.error(f"❌ Parent directory: {os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}")
    raise ImportError(f"Cannot import agent module: {e}")
```

#### **Multiple Import Locations Fixed**
1. **`get_graph_visualization_data()`** - Direct Neo4j queries
2. **`get_hybrid_graph_data()`** - Hybrid Graphiti + Neo4j queries  
3. **`get_neo4j_data_for_entities()`** - Entity-specific queries

### **3. Added Debug Endpoint**

#### **Agent Import Test Endpoint**
```python
@app.route('/debug/agent-import')
def debug_agent_import():
    """Debug endpoint to test agent module import."""
    try:
        logger.info("🔍 Testing agent module import...")
        logger.info(f"📂 Current working directory: {os.getcwd()}")
        logger.info(f"📂 Web UI file location: {os.path.abspath(__file__)}")
        logger.info(f"📂 Parent directory: {os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}")
        logger.info(f"📋 Current sys.path: {sys.path[:5]}...")
        
        from agent.graph_utils import get_neo4j_driver
        logger.info("✅ Successfully imported agent.graph_utils.get_neo4j_driver")
        
        # Test Neo4j connection
        driver = get_neo4j_driver()
        logger.info("✅ Successfully obtained Neo4j driver")
        
        with driver.session() as session:
            result = session.run("RETURN 1 as test")
            record = result.single()
            test_value = record["test"] if record else None
            logger.info(f"✅ Neo4j connection test result: {test_value}")
        
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
```

## Technical Details

### **Path Resolution Logic**
```python
# Current file: /project/web_ui/app.py
current_file = os.path.abspath(__file__)
# Result: /project/web_ui/app.py

web_ui_dir = os.path.dirname(current_file)
# Result: /project/web_ui

parent_dir = os.path.dirname(web_ui_dir)
# Result: /project

# Add parent directory to sys.path
sys.path.insert(0, parent_dir)
# Now Python can find: /project/agent/
```

### **Import Resolution**
```python
# Before fix:
from agent.graph_utils import get_neo4j_driver
# Error: ModuleNotFoundError: No module named 'agent'

# After fix:
setup_agent_import()  # Adds /project to sys.path
from agent.graph_utils import get_neo4j_driver
# Success: Finds /project/agent/graph_utils.py
```

### **Error Handling Strategy**
1. **Detailed logging** - Show all relevant paths and sys.path
2. **Graceful failure** - Provide clear error messages
3. **Debug information** - Include working directory and file locations
4. **Test endpoint** - Verify import and connection separately

## Expected Results

### **Before Fix**
```
Request: GET /api/graph/neo4j/visualize?depth=3&entity=HKJC
Error: Failed to fetch Neo4j graph data: No module named 'agent'
Response: 200 OK (but with error in data)
```

### **After Fix**
```
Request: GET /api/graph/neo4j/visualize?depth=3&entity=HKJC
Logs:
  🔍 Graph visualization request: entity='HKJC', depth=3
  📡 Using direct Neo4j approach for entity: HKJC
  🔍 Fetching Neo4j graph data for entity: 'HKJC', depth: 3
  ✅ Neo4j driver obtained
  📡 Neo4j session created
  🎯 Searching for entity-centered graph: HKJC
  📊 Raw data from Neo4j: 5 nodes, 8 relationships
  ✅ Successfully processed Neo4j data: 5 nodes, 8 relationships
Response: 200 OK with actual graph data
```

### **Debug Endpoint Test**
```
Request: GET /debug/agent-import
Response: {
  "status": "success",
  "message": "Agent module import and Neo4j connection successful",
  "test_query_result": 1,
  "working_directory": "/project",
  "web_ui_location": "/project/web_ui/app.py",
  "parent_directory": "/project"
}
```

## Benefits

### ✅ **Resolved Import Issues**
- **Agent module accessible** from web UI
- **Neo4j utilities available** for graph visualization
- **Cross-directory imports working** properly
- **Consistent import behavior** across all functions

### ✅ **Enhanced Debugging**
- **Detailed error logging** for import failures
- **Path information** for troubleshooting
- **Test endpoint** for verification
- **Clear error messages** for diagnosis

### ✅ **Improved Reliability**
- **Graceful error handling** for import failures
- **Comprehensive logging** for troubleshooting
- **Robust path setup** for different deployment scenarios
- **Consistent behavior** across environments

### ✅ **Better Maintainability**
- **Centralized path setup** in one location
- **Reusable import configuration** for future modules
- **Clear documentation** of import requirements
- **Easy debugging** with test endpoint

## Testing

### **Manual Testing Steps**
1. **Test debug endpoint**: `GET /debug/agent-import`
2. **Verify import success**: Check response status and logs
3. **Test graph visualization**: `GET /api/graph/neo4j/visualize?depth=3&entity=HKJC`
4. **Check server logs**: Verify no import errors

### **Expected Debug Output**
```
INFO - 🔍 Testing agent module import...
INFO - 📂 Current working directory: /project
INFO - 📂 Web UI file location: /project/web_ui/app.py
INFO - 📂 Parent directory: /project
INFO - 📋 Current sys.path: ['/project', '/usr/lib/python3.x', ...]
INFO - ✅ Successfully imported agent.graph_utils.get_neo4j_driver
INFO - ✅ Successfully obtained Neo4j driver
INFO - ✅ Neo4j connection test result: 1
```

## Deployment Impact

### **Immediate Benefits**
After deploying this fix:
1. ✅ **Graph visualization API will work** without import errors
2. ✅ **Neo4j queries will execute** successfully
3. ✅ **Entity searches will return data** from the graph database
4. ✅ **Debug endpoint available** for troubleshooting

### **Long-term Improvements**
- **Reliable cross-module imports** for future development
- **Better error handling** for deployment issues
- **Enhanced debugging capabilities** for production troubleshooting
- **Consistent import behavior** across different environments

The fix ensures that the web UI can properly import and use the agent module's Neo4j utilities, enabling successful graph visualization for entities like "Man Ieng IM", "HKJC", and others.
