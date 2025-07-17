# Neo4j Session Database Parameter Fix

## Problem Identified

The web UI was failing to create Neo4j sessions because the `session()` method requires a `database` parameter:

```
ERROR:app:❌ Failed to fetch Neo4j graph data: Neo4jDriver.session() missing 1 required positional argument: 'database'
TypeError: Neo4jDriver.session() missing 1 required positional argument: 'database'
```

**Root Cause:**
- Neo4j driver's `session()` method requires a database name parameter
- The web UI was calling `driver.session()` without specifying the database
- No database configuration was available in the GraphitiClient
- Modern Neo4j drivers require explicit database specification

## Solution Implemented

### **1. Added Database Configuration**

#### **Enhanced GraphitiClient with Database Support**
```python
# Added to GraphitiClient.__init__()
self.neo4j_database = os.getenv("NEO4J_DATABASE", "neo4j")  # Default database name
```

#### **Environment Variable Support**
- **`NEO4J_DATABASE`**: Configurable database name (defaults to "neo4j")
- **Backward compatibility**: Uses standard "neo4j" database if not specified
- **Flexible configuration**: Can be overridden via environment variables

### **2. Created Session Management Functions**

#### **Added Async Session Function**
```python
async def get_neo4j_session():
    """
    Get a Neo4j session with the correct database.
    
    Returns:
        Neo4j session instance
    """
    driver = await get_neo4j_driver()
    database = get_neo4j_database()
    return driver.session(database=database)
```

#### **Added Synchronous Session Function**
```python
def get_neo4j_session_sync():
    """
    Get a Neo4j session synchronously with the correct database.
    
    Returns:
        Neo4j session instance
    """
    import asyncio
    
    # Handle async/sync bridge with proper event loop management
    try:
        loop = asyncio.get_running_loop()
        # Create new event loop in thread if needed
        def get_session():
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                return new_loop.run_until_complete(get_neo4j_session())
            finally:
                new_loop.close()
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(get_session)
            return future.result()
            
    except RuntimeError:
        # No event loop running, create one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(get_neo4j_session())
        finally:
            loop.close()
```

#### **Added Database Name Function**
```python
def get_neo4j_database():
    """
    Get the Neo4j database name.
    
    Returns:
        Neo4j database name
    """
    client = get_graph_client()
    return client.neo4j_database
```

### **3. Updated Web UI Session Usage**

#### **Replaced Direct Driver Usage**
```python
# Before (Incorrect - missing database parameter)
driver = get_neo4j_driver_sync()
with driver.session() as session:
    result = session.run(query)

# After (Correct - uses proper session with database)
session = get_neo4j_session_sync()
try:
    result = session.run(query)
finally:
    session.close()
```

#### **Updated All Session Locations**
1. **`get_graph_visualization_data()`** - Direct Neo4j queries
2. **`get_neo4j_data_for_entities()`** - Entity-specific queries
3. **`debug_agent_import()`** - Debug endpoint testing

#### **Added Proper Session Management**
```python
session = get_neo4j_session_sync()
try:
    # Use session for queries
    result = session.run(query, parameters)
    # Process results
finally:
    # Always close session
    try:
        session.close()
        logger.info(f"✅ Neo4j session closed")
    except Exception as e:
        logger.warning(f"⚠️ Failed to close Neo4j session: {e}")
```

## Technical Implementation

### **Database Configuration Flow**
```python
# 1. Environment variable or default
database_name = os.getenv("NEO4J_DATABASE", "neo4j")

# 2. Store in GraphitiClient
self.neo4j_database = database_name

# 3. Access via helper function
def get_neo4j_database():
    client = get_graph_client()
    return client.neo4j_database

# 4. Use in session creation
driver = await get_neo4j_driver()
database = get_neo4j_database()
session = driver.session(database=database)
```

### **Session Lifecycle Management**
```python
# 1. Get session with correct database
session = get_neo4j_session_sync()

# 2. Use session for queries
try:
    result = session.run("MATCH (n) RETURN n LIMIT 10")
    records = list(result)
    
# 3. Always close session
finally:
    session.close()
```

### **Error Handling Enhancement**
```python
try:
    session = get_neo4j_session_sync()
    logger.info(f"✅ Neo4j session obtained")
    
    # Query execution
    result = session.run(query, parameters)
    
finally:
    # Ensure session cleanup
    try:
        session.close()
        logger.info(f"✅ Neo4j session closed")
    except Exception as e:
        logger.warning(f"⚠️ Failed to close Neo4j session: {e}")
```

## Expected Results

### **Before Fix**
```
Request: GET /api/graph/neo4j/visualize?depth=3&entity=Man+Ieng+IM
Error: TypeError: Neo4jDriver.session() missing 1 required positional argument: 'database'
Response: 200 OK (but with error data)
```

### **After Fix**
```
Request: GET /api/graph/neo4j/visualize?depth=3&entity=Man+Ieng+IM
Logs:
  🔍 Graph visualization request: entity='Man Ieng IM', depth=3
  📡 Using direct Neo4j approach for entity: Man Ieng IM
  🔍 Fetching Neo4j graph data for entity: 'Man Ieng IM', depth: 3
  ✅ Neo4j session obtained
  📡 Neo4j session created
  🎯 Searching for entity-centered graph: Man Ieng IM
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
```

## Configuration

### **Environment Variables**
```bash
# Optional: Specify Neo4j database name (defaults to "neo4j")
export NEO4J_DATABASE=neo4j

# Required: Neo4j connection details
export NEO4J_URI=bolt://localhost:7687
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=your_password
```

### **Default Configuration**
- **Database**: "neo4j" (standard default database)
- **URI**: "bolt://localhost:7687"
- **User**: "neo4j"
- **Password**: From environment variable (required)

## Benefits

### ✅ **Resolved Session Creation Issues**
- **Proper database parameter** - Sessions created with correct database name
- **Modern Neo4j compatibility** - Works with current Neo4j driver requirements
- **Flexible configuration** - Database name configurable via environment
- **Backward compatibility** - Uses standard "neo4j" database by default

### ✅ **Enhanced Session Management**
- **Proper lifecycle** - Sessions created and closed correctly
- **Resource cleanup** - Prevents session leaks
- **Error handling** - Graceful session closure even on errors
- **Logging** - Clear session creation and closure tracking

### ✅ **Improved Architecture**
- **Centralized session creation** - Single point for session management
- **Async/sync support** - Both async and sync session functions
- **Reusable functions** - Can be used across different modules
- **Clean separation** - Database configuration separate from usage

### ✅ **Better Debugging**
- **Session lifecycle logging** - Track session creation and closure
- **Database configuration visibility** - Clear database name logging
- **Error details** - Specific error messages for session issues
- **Test endpoint** - Verify session creation and queries

## Testing

### **Manual Testing Steps**
1. **Test debug endpoint**: `GET /debug/agent-import`
   - Should return success with test_query_result: 1
   - Should log session creation and closure
2. **Test graph visualization**: `GET /api/graph/neo4j/visualize?depth=3&entity=Man+Ieng+IM`
   - Should return actual graph data without session errors
   - Should log proper session management
3. **Check server logs**: Verify session creation and closure messages
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
1. ✅ **Graph visualization API will work** without session creation errors
2. ✅ **Neo4j queries will execute** with proper database sessions
3. ✅ **Session management** will be handled correctly
4. ✅ **Resource cleanup** will prevent session leaks

### **Long-term Improvements**
- **Stable Neo4j integration** for all web UI operations
- **Proper resource management** preventing connection issues
- **Configurable database support** for different environments
- **Enhanced monitoring** with session lifecycle logging

The fix ensures that the web UI can properly create and manage Neo4j sessions with the correct database parameter, enabling successful graph visualization for entities like "Man Ieng IM" and others.
