# Neo4j Synchronous Driver Fix

## Problem Identified

The web UI was still failing with async session issues despite previous fixes:

```
ERROR:app:❌ Failed to fetch Neo4j graph data: 'coroutine' object has no attribute 'single'
AttributeError: 'coroutine' object has no attribute 'single'

/Users/he/PycharmProjects/llm-entity-graph/web_ui/app.py:506: RuntimeWarning: coroutine 'AsyncSession.run' was never awaited
  graph_data = get_graph_visualization_data(entity, depth)
```

**Root Cause:**
- **Graphiti driver is async** - The driver from Graphiti client was inherently async
- **Session.run() returns coroutine** - Even with "sync" session, methods were async
- **Mixed driver types** - Attempting to use async driver in sync context
- **Incomplete separation** - Previous fix didn't fully separate from Graphiti's async driver

## Solution Implemented

### **1. Created Independent Synchronous Driver**

#### **Problem: Dependency on Graphiti's Async Driver**
```python
# Before (Still using Graphiti's async driver)
def get_neo4j_session_sync():
    driver = get_neo4j_driver_sync()  # This was still Graphiti's async driver
    database = get_neo4j_database()
    return driver.session(database=database)  # ❌ Still async session
```

#### **Solution: Independent Sync Driver Creation**
```python
# After (Complete independence from Graphiti driver)
def get_neo4j_driver_sync():
    """Get a synchronous Neo4j driver (for use in non-async contexts)."""
    from neo4j import GraphDatabase
    
    # Get Neo4j configuration
    client = get_graph_client()
    
    # Create a new synchronous driver directly
    return GraphDatabase.driver(
        client.neo4j_uri,
        auth=(client.neo4j_user, client.neo4j_password)
    )

def get_neo4j_session_sync():
    """Get a Neo4j session synchronously with the correct database."""
    from neo4j import GraphDatabase
    
    # Get Neo4j configuration
    client = get_graph_client()
    
    # Create a new synchronous driver directly
    sync_driver = GraphDatabase.driver(
        client.neo4j_uri,
        auth=(client.neo4j_user, client.neo4j_password)
    )
    
    # Create a synchronous session
    return sync_driver.session(database=client.neo4j_database)
```

### **2. Enhanced Session and Driver Management**

#### **Created Combined Session/Driver Functions**
```python
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
```

### **3. Updated All Session Usage**

#### **New Session Pattern**
```python
# Before (Problematic - using Graphiti's async driver)
session = get_neo4j_session_sync()  # Still async under the hood
try:
    result = session.run(query)  # ❌ Returns coroutine
    record = result.single()    # ❌ AttributeError: 'coroutine' has no 'single'
finally:
    close_neo4j_session(session)

# After (Correct - independent sync driver)
session, driver = get_neo4j_session_with_driver()  # Pure sync driver/session
try:
    result = session.run(query)  # ✅ Returns sync result
    record = result.single()    # ✅ Works correctly
finally:
    close_neo4j_session_and_driver(session, driver)  # ✅ Proper cleanup
```

#### **Updated All Functions**
1. **`get_graph_visualization_data()`** - Main graph visualization queries
2. **`get_neo4j_data_for_entities()`** - Entity-specific queries
3. **`debug_agent_import()`** - Debug endpoint testing

## Technical Details

### **Driver Architecture Separation**

#### **Graphiti Driver (Async)**
```python
# Graphiti creates async driver for its own use
self.graphiti = Graphiti(
    self.neo4j_uri,
    self.neo4j_user, 
    self.neo4j_password,
    # ... other config
)
# self.graphiti.driver is async
```

#### **Web UI Driver (Sync)**
```python
# Web UI creates independent sync driver
from neo4j import GraphDatabase

sync_driver = GraphDatabase.driver(
    neo4j_uri,
    auth=(neo4j_user, neo4j_password)
)
# sync_driver is synchronous
```

### **Session Type Differences**

#### **Async Session (Graphiti)**
```python
# All methods return coroutines
async_session = await async_driver.session(database=database)
result_coroutine = async_session.run(query)  # Returns coroutine
result = await result_coroutine              # Need to await
record = await result.single()              # Need to await
```

#### **Sync Session (Web UI)**
```python
# All methods return results directly
sync_session = sync_driver.session(database=database)
result = sync_session.run(query)            # Returns result object
record = result.single()                    # Returns record directly
```

### **Resource Management**

#### **Proper Cleanup Order**
```python
def close_neo4j_session_and_driver(session, driver):
    try:
        # 1. Close session first
        if session and hasattr(session, 'close'):
            session.close()
        
        # 2. Close driver second
        if driver and hasattr(driver, 'close'):
            driver.close()
            
        logger.info(f"✅ Neo4j session and driver closed")
    except Exception as e:
        logger.warning(f"⚠️ Failed to close Neo4j session/driver: {e}")
```

## Expected Results

### **Before Fix**
```
Request: GET /api/graph/neo4j/visualize?depth=3&entity=Dennis+Pok+Man+LUI
Error: AttributeError: 'coroutine' object has no attribute 'single'
RuntimeWarning: coroutine 'AsyncSession.run' was never awaited
Response: 200 OK (but with error data)
```

### **After Fix**
```
Request: GET /api/graph/neo4j/visualize?depth=3&entity=Dennis+Pok+Man+LUI
Logs:
  🔍 Graph visualization request: entity='Dennis Pok Man LUI', depth=3
  📡 Using direct Neo4j approach for entity: Dennis Pok Man LUI
  ✅ Neo4j session and driver obtained
  📡 Neo4j session created
  🎯 Searching for entity-centered graph: Dennis Pok Man LUI
  📝 Executing query: MATCH path = (center)-[*1..3]-(connected)...
  📋 Query result record: True/False
  📊 Raw data from Neo4j: X nodes, Y relationships
  ✅ Successfully processed Neo4j data: X nodes, Y relationships
  ✅ Neo4j session and driver closed
Response: 200 OK with actual graph data
```

### **Debug Endpoint Test**
```
Request: GET /debug/agent-import
Expected Response: {
  "status": "success",
  "message": "Agent module import and Neo4j connection successful",
  "test_query_result": 1
}

Expected Logs:
  ✅ Successfully imported agent.graph_utils functions
  ✅ Successfully obtained Neo4j session and driver
  ✅ Neo4j connection test result: 1
  ✅ Neo4j session and driver closed
```

## Benefits

### ✅ **Complete Async/Sync Separation**
- **Independent sync driver** - No dependency on Graphiti's async driver
- **Pure synchronous operations** - All session methods return results directly
- **No coroutine errors** - Eliminates 'coroutine' object attribute errors
- **No runtime warnings** - No more async warnings in Flask context

### ✅ **Enhanced Resource Management**
- **Proper driver cleanup** - Both session and driver closed correctly
- **Resource leak prevention** - Ensures all connections are released
- **Error handling** - Graceful failure with clear error messages
- **Lifecycle management** - Clear creation and cleanup patterns

### ✅ **Improved Reliability**
- **Consistent behavior** - Same sync pattern across all functions
- **Flask compatibility** - Perfect fit for synchronous web framework
- **Error elimination** - No more async/sync conflicts
- **Performance** - Direct sync operations without async overhead

### ✅ **Better Architecture**
- **Clear separation** - Graphiti uses async, Web UI uses sync
- **Independent operation** - Web UI doesn't depend on Graphiti's driver state
- **Maintainable code** - Simple, straightforward sync patterns
- **Future-proof** - Easy to extend for other sync operations

## Testing

### **Manual Testing Steps**
1. **Test debug endpoint**: `GET /debug/agent-import`
   - Should return success without any async warnings
   - Should log proper session and driver management
2. **Test graph visualization**: `GET /api/graph/neo4j/visualize?depth=3&entity=Dennis+Pok+Man+LUI`
   - Should return actual graph data without coroutine errors
   - Should log session creation and cleanup
3. **Check server logs**: Verify no RuntimeWarnings about coroutines
4. **Test web UI**: Use graph visualization interface

### **Expected Session Logs**
```
INFO - ✅ Neo4j session and driver obtained
INFO - 📡 Neo4j session created
INFO - 📝 Executing query: MATCH path = ...
INFO - 📊 Raw data from Neo4j: X nodes, Y relationships
INFO - ✅ Successfully processed Neo4j data
INFO - ✅ Neo4j session and driver closed
```

## Deployment Impact

### **Immediate Benefits**
After deploying this fix:
1. ✅ **Graph visualization API will work** without any async session errors
2. ✅ **No more coroutine warnings** in server logs
3. ✅ **Proper resource management** with session and driver cleanup
4. ✅ **Reliable Neo4j queries** returning actual data consistently

### **Long-term Improvements**
- **Stable Neo4j integration** independent of Graphiti's async operations
- **Clean architecture** with proper async/sync separation
- **Enhanced performance** with direct sync operations
- **Maintainable codebase** with consistent patterns

The fix ensures complete separation between Graphiti's async Neo4j operations and the web UI's synchronous requirements, eliminating all async/sync conflicts and enabling reliable graph visualization for entities like "Dennis Pok Man LUI" and others.
