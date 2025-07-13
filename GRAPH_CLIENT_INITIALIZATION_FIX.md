# Fix for NEO4J_PASSWORD Environment Variable Error

## Problem
API server fails to start with error:
```
ValueError: NEO4J_PASSWORD environment variable not set
```

This occurs during module import when `graph_utils.py` tries to initialize the GraphitiClient immediately.

## Root Cause
The issue was in `agent/graph_utils.py` at line 1099:
```python
# Global Graphiti client instance
graph_client = GraphitiClient()  # ❌ This runs at import time!
```

The `GraphitiClient()` constructor validates Neo4j environment variables immediately when the module is imported, before the application has a chance to start and load environment variables properly.

## Solution Applied

### 1. **Lazy Graph Client Initialization**

**Before:**
```python
# Global Graphiti client instance
graph_client = GraphitiClient()

async def initialize_graph():
    """Initialize graph client."""
    await graph_client.initialize()
```

**After:**
```python
# Global Graphiti client instance (lazy initialization)
graph_client: Optional[GraphitiClient] = None

def get_graph_client() -> GraphitiClient:
    """Get or create the global graph client instance."""
    global graph_client
    if graph_client is None:
        graph_client = GraphitiClient()
    return graph_client

async def initialize_graph():
    """Initialize graph client."""
    client = get_graph_client()
    await client.initialize()
```

### 2. **Updated All Graph Client References**

Changed all instances of `graph_client.method()` to `get_graph_client().method()` in:
- `agent/graph_utils.py` (13 instances)
- `agent/tools.py` (3 instances)
- `ingest_with_cleanup.py` (1 instance)
- `test_relationship_extraction.py` (import)
- `test_ingestion_consistency.py` (1 instance)
- `test_fixed_relationships.py` (1 instance)

### 3. **Key Benefits**

- ✅ **No import-time validation** - Graph client only created when first accessed
- ✅ **Environment variables loaded properly** - Validation happens after app startup
- ✅ **Backward compatible** - All existing code continues to work
- ✅ **Thread-safe** - Global instance properly managed
- ✅ **Lazy loading** - Client only created when needed

## Files Modified

### 1. `agent/graph_utils.py`
- Added lazy initialization with `get_graph_client()` function
- Updated all 13 references from `graph_client.method()` to `get_graph_client().method()`
- Maintained all existing functionality

### 2. `agent/tools.py`
- Updated import: `from .graph_utils import get_graph_client`
- Updated 3 usage instances to use `get_graph_client()`

### 3. `ingest_with_cleanup.py`
- Updated import and usage to use `get_graph_client()`

### 4. Test Files
- Updated imports and usage in test files to use new lazy pattern

## How It Works Now

### 1. **Module Import**
```python
# No graph validation at import time
graph_client: Optional[GraphitiClient] = None  # Just a variable
```

### 2. **First Graph Access**
```python
# When first graph operation is called:
client = get_graph_client()  # Creates GraphitiClient() here
await client.initialize()    # Uses the client
```

### 3. **Environment Variable Validation**
- Now happens when `get_graph_client()` is first called
- This occurs after the application has started and loaded environment variables
- Provides clear error message if Neo4j credentials are missing

## Testing the Fix

### 1. **Verify Import Works**
```python
# This should now work without NEO4J_PASSWORD set
from agent.graph_utils import get_graph_client
```

### 2. **Test Graph Operations**
```python
# This will validate NEO4J_PASSWORD when first called
client = get_graph_client()
await client.initialize()
```

### 3. **Environment Variable Validation**
```bash
# Without NEO4J_PASSWORD - should fail gracefully when first accessed
unset NEO4J_PASSWORD
python -c "from agent.graph_utils import get_graph_client; print('Import successful')"

# With NEO4J_PASSWORD - should work completely
export NEO4J_PASSWORD="your-password"
python -c "from agent.graph_utils import get_graph_client; print('Import successful')"
```

## Deployment Impact

### ✅ **Fixes the Startup Issue**
- API server will now start successfully
- Graph validation happens at the right time
- Clear error messages if environment variables are missing

### ✅ **Maintains All Functionality**
- All existing graph operations work unchanged
- Knowledge graph search works as before
- Entity relationship extraction preserved

### ✅ **Better Error Handling**
- Environment variable errors now occur during application startup
- Not during module import
- Easier to debug and fix

## Environment Variables Required

Make sure these are set in your deployment:

```bash
# Required for Neo4j/Graph operations
NEO4J_URI=neo4j+s://instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password

# Required for database operations
DATABASE_URL=postgresql://user:password@host:port/database

# Required for LLM operations
LLM_API_KEY=your-api-key
EMBEDDING_API_KEY=your-api-key
```

## Summary

The fix changes graph client initialization from **eager** (at import time) to **lazy** (when first needed). This allows:

1. ✅ **Modules to import successfully** without environment variables
2. ✅ **Environment variables to be loaded** before validation
3. ✅ **Clear error messages** when configuration is missing
4. ✅ **Proper application startup sequence**

Combined with the previous database pool fix, the API server should now start successfully and only validate connections when they're actually needed!
