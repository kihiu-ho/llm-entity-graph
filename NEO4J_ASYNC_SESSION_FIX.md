# Neo4j Async Session Fix

## Problem Identified

The web UI was failing with async session issues when trying to query Neo4j:

```
ERROR:app:❌ Failed to fetch Neo4j graph data: 'coroutine' object has no attribute 'single'
AttributeError: 'coroutine' object has no attribute 'single'

/Users/he/PycharmProjects/llm-entity-graph/web_ui/app.py:640: RuntimeWarning: coroutine 'AsyncSession.close' was never awaited
  session.close()
RuntimeWarning: Enable tracemalloc to get the object allocation traceback
```

**Root Causes:**
1. **Async session returned** - `get_neo4j_session_sync()` was returning an async session
2. **Coroutine not awaited** - `session.run()` returned a coroutine instead of a result
3. **Async session.close()** - Session close method was async but called synchronously
4. **Mixed async/sync context** - Flask web UI is synchronous but Neo4j session was async

## Solution Implemented

### **1. Fixed Synchronous Session Creation**

#### **Problem: Async Session in Sync Context**
```python
# Before (Incorrect - returned async session)
def get_neo4j_session_sync():
    # This was returning an async session from get_neo4j_session()
    return loop.run_until_complete(get_neo4j_session())  # ❌ Async session
```

#### **Solution: Direct Synchronous Session**
```python
# After (Correct - creates sync session directly)
def get_neo4j_session_sync():
    """
    Get a Neo4j session synchronously with the correct database.
    
    Returns:
        Synchronous Neo4j session instance
    """
    # Get the driver synchronously
    driver = get_neo4j_driver_sync()
    database = get_neo4j_database()
    
    # Create a synchronous session directly from the driver
    return driver.session(database=database)
```

### **2. Enhanced Session Management**

#### **Created Helper Function**
```python
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
```

#### **Updated Session Usage Pattern**
```python
# Before (Problematic)
session = get_neo4j_session_sync()  # Returned async session
try:
    result = session.run(query)  # Returned coroutine
    record = result.single()    # ❌ AttributeError: 'coroutine' has no 'single'
finally:
    session.close()  # ❌ RuntimeWarning: coroutine not awaited

# After (Correct)
session = get_neo4j_session_sync()  # Returns sync session
try:
    result = session.run(query)  # Returns sync result
    record = result.single()    # ✅ Works correctly
finally:
    close_neo4j_session(session)  # ✅ Handles both sync/async properly
```

### **3. Fixed All Session Locations**

#### **Updated Functions**
1. **`get_graph_visualization_data()`** - Main graph visualization queries
2. **`get_neo4j_data_for_entities()`** - Entity-specific queries
3. **`debug_agent_import()`** - Debug endpoint testing

#### **Consistent Session Pattern**
```python
# Standard pattern used across all functions
try:
    from agent.graph_utils import get_neo4j_session_sync
except ImportError as e:
    logger.error(f"❌ Failed to import agent.graph_utils: {e}")
    raise ImportError(f"Cannot import agent module: {e}")

session = get_neo4j_session_sync()
logger.info(f"✅ Neo4j session obtained")

try:
    # Use session for queries
    result = session.run(query, parameters)
    record = result.single()
    # Process results
finally:
    # Always close session properly
    close_neo4j_session(session)
```

## Technical Details

### **Session Type Differences**

#### **Async Session (Before)**
```python
# Async session methods return coroutines
async_session = await driver.session(database=database)
result_coroutine = async_session.run(query)  # Returns coroutine
result = await result_coroutine              # Need to await
record = await result.single()              # Need to await
await async_session.close()                 # Need to await
```

#### **Sync Session (After)**
```python
# Sync session methods return results directly
sync_session = driver.session(database=database)
result = sync_session.run(query)            # Returns result object
record = result.single()                    # Returns record directly
sync_session.close()                        # Closes synchronously
```

### **Driver vs Session Creation**

#### **Driver Creation (Async)**
```python
# Driver creation requires async initialization
async def get_neo4j_driver():
    client = get_graph_client()
    if not client._initialized:
        await client.initialize()  # Async initialization required
    return client.graphiti.driver
```

#### **Session Creation (Can be Sync)**
```python
# Once driver exists, sessions can be created synchronously
def get_neo4j_session_sync():
    driver = get_neo4j_driver_sync()  # Get driver synchronously
    database = get_neo4j_database()
    return driver.session(database=database)  # Create sync session
```

### **Error Handling Enhancement**

#### **Robust Session Closing**
```python
def close_neo4j_session(session):
    """Handles both sync and async session closing."""
    try:
        if hasattr(session, 'close'):
            if asyncio.iscoroutinefunction(session.close):
                # Handle async session
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(session.close())
                finally:
                    loop.close()
            else:
                # Handle sync session
                session.close()
        logger.info(f"✅ Neo4j session closed")
    except Exception as e:
        logger.warning(f"⚠️ Failed to close Neo4j session: {e}")
```

## Expected Results

### **Before Fix**
```
Request: GET /api/graph/neo4j/visualize?depth=3&entity=Dennis+Pok+Man+LUI
Error: AttributeError: 'coroutine' object has no attribute 'single'
RuntimeWarning: coroutine 'AsyncSession.close' was never awaited
Response: 200 OK (but with error data)
```

### **After Fix**
```
Request: GET /api/graph/neo4j/visualize?depth=3&entity=Dennis+Pok+Man+LUI
Logs:
  🔍 Graph visualization request: entity='Dennis Pok Man LUI', depth=3
  📡 Using direct Neo4j approach for entity: Dennis Pok Man LUI
  ✅ Neo4j session obtained
  📡 Neo4j session created
  🎯 Searching for entity-centered graph: Dennis Pok Man LUI
  📝 Executing query: MATCH path = (center)-[*1..3]-(connected)...
  📋 Query result record: True/False
  📊 Raw data from Neo4j: X nodes, Y relationships
  ✅ Successfully processed Neo4j data: X nodes, Y relationships
  ✅ Neo4j session closed
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
  ✅ Successfully imported agent.graph_utils.get_neo4j_session_sync
  ✅ Successfully obtained Neo4j session
  ✅ Neo4j connection test result: 1
  ✅ Neo4j session closed
```

## Benefits

### ✅ **Resolved Async/Sync Issues**
- **Proper sync sessions** - No more coroutine errors
- **Correct method calls** - `result.single()` works as expected
- **No runtime warnings** - Session closing handled properly
- **Flask compatibility** - Synchronous sessions work in Flask context

### ✅ **Enhanced Session Management**
- **Robust closing** - Handles both sync and async sessions
- **Error handling** - Graceful failure with clear error messages
- **Resource cleanup** - Prevents session leaks
- **Consistent pattern** - Same approach across all functions

### ✅ **Improved Reliability**
- **No coroutine errors** - Synchronous operations throughout
- **Proper resource management** - Sessions created and closed correctly
- **Better error messages** - Clear indication of session issues
- **Future-proof design** - Handles both session types

### ✅ **Better Debugging**
- **Session lifecycle logging** - Track creation and closure
- **Error details** - Specific error messages for session issues
- **Test endpoint** - Verify session creation and queries
- **Warning elimination** - No more async warnings

## Testing

### **Manual Testing Steps**
1. **Test debug endpoint**: `GET /debug/agent-import`
   - Should return success without async warnings
   - Should log proper session management
2. **Test graph visualization**: `GET /api/graph/neo4j/visualize?depth=3&entity=Dennis+Pok+Man+LUI`
   - Should return actual graph data without coroutine errors
   - Should log session creation and closure
3. **Check server logs**: Verify no RuntimeWarnings about coroutines
4. **Test web UI**: Use graph visualization interface

### **Expected Session Logs**
```
INFO - ✅ Neo4j session obtained
INFO - 📡 Neo4j session created
INFO - 📝 Executing query: MATCH path = ...
INFO - 📊 Raw data from Neo4j: X nodes, Y relationships
INFO - ✅ Successfully processed Neo4j data
INFO - ✅ Neo4j session closed
```

## Deployment Impact

### **Immediate Benefits**
After deploying this fix:
1. ✅ **Graph visualization API will work** without async session errors
2. ✅ **No more coroutine warnings** in server logs
3. ✅ **Proper session management** with correct resource cleanup
4. ✅ **Reliable Neo4j queries** returning actual data

### **Long-term Improvements**
- **Stable Neo4j integration** for all web UI operations
- **Proper async/sync separation** for Flask compatibility
- **Enhanced error handling** for session management
- **Consistent session patterns** across the application

The fix ensures that the web UI can properly create and use synchronous Neo4j sessions, eliminating async/sync conflicts and enabling successful graph visualization for entities like "Dennis Pok Man LUI" and others.
