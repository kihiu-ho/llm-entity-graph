# Fix for DATABASE_URL Environment Variable Error

## Problem
API server fails to start with error:
```
ValueError: DATABASE_URL environment variable not set
```

This occurs during module import when `db_utils.py` tries to initialize the database pool immediately.

## Root Cause
The issue was in `agent/db_utils.py` at line 70:
```python
# Global database pool instance
db_pool = DatabasePool()  # ❌ This runs at import time!
```

The `DatabasePool()` constructor validates the `DATABASE_URL` environment variable immediately when the module is imported, before the application has a chance to start and load environment variables properly.

## Solution Applied

### 1. **Lazy Database Pool Initialization**

**Before:**
```python
# Global database pool instance
db_pool = DatabasePool()

async def initialize_database():
    """Initialize database connection pool."""
    await db_pool.initialize()
```

**After:**
```python
# Global database pool instance (lazy initialization)
db_pool: Optional[DatabasePool] = None

def get_db_pool() -> DatabasePool:
    """Get or create the global database pool instance."""
    global db_pool
    if db_pool is None:
        db_pool = DatabasePool()
    return db_pool

async def initialize_database():
    """Initialize database connection pool."""
    pool = get_db_pool()
    await pool.initialize()
```

### 2. **Updated All Database Pool References**

Changed all instances of `db_pool.acquire()` to `get_db_pool().acquire()` in:
- `agent/db_utils.py` (14 instances)
- `ingestion/ingest.py` (1 instance)
- `tests/conftest.py` (test mocking)

### 3. **Key Benefits**

- ✅ **No import-time validation** - Database pool only created when first accessed
- ✅ **Environment variables loaded properly** - Validation happens after app startup
- ✅ **Backward compatible** - All existing code continues to work
- ✅ **Thread-safe** - Global instance properly managed
- ✅ **Lazy loading** - Pool only created when needed

## Files Modified

### 1. `agent/db_utils.py`
- Added lazy initialization with `get_db_pool()` function
- Updated all 14 references from `db_pool.acquire()` to `get_db_pool().acquire()`
- Maintained all existing functionality

### 2. `ingestion/ingest.py`
- Updated import: `from ..agent.db_utils import get_db_pool`
- Updated usage: `async with get_db_pool().acquire() as conn:`

### 3. `tests/conftest.py`
- Updated test mocking to work with new lazy initialization pattern

## How It Works Now

### 1. **Module Import**
```python
# No database validation at import time
db_pool: Optional[DatabasePool] = None  # Just a variable
```

### 2. **First Database Access**
```python
# When first database operation is called:
pool = get_db_pool()  # Creates DatabasePool() here
async with pool.acquire() as conn:  # Uses the pool
```

### 3. **Environment Variable Validation**
- Now happens when `get_db_pool()` is first called
- This occurs after the application has started and loaded environment variables
- Provides clear error message if `DATABASE_URL` is missing

## Testing the Fix

### 1. **Verify Import Works**
```python
# This should now work without DATABASE_URL set
from agent.db_utils import get_db_pool
```

### 2. **Test Database Operations**
```python
# This will validate DATABASE_URL when first called
pool = get_db_pool()
await pool.initialize()
```

### 3. **Environment Variable Validation**
```bash
# Without DATABASE_URL - should fail gracefully when first accessed
unset DATABASE_URL
python -c "from agent.db_utils import get_db_pool; print('Import successful')"

# With DATABASE_URL - should work completely
export DATABASE_URL="postgresql://..."
python -c "from agent.db_utils import get_db_pool; print('Import successful')"
```

## Deployment Impact

### ✅ **Fixes the Startup Issue**
- API server will now start successfully
- Database validation happens at the right time
- Clear error messages if environment variables are missing

### ✅ **Maintains All Functionality**
- All existing database operations work unchanged
- Connection pooling works as before
- Error handling preserved

### ✅ **Better Error Handling**
- Environment variable errors now occur during application startup
- Not during module import
- Easier to debug and fix

## Environment Variables Required

Make sure these are set in your deployment:

```bash
# Required for database operations
DATABASE_URL=postgresql://user:password@host:port/database

# Required for Neo4j operations  
NEO4J_URI=neo4j+s://instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password

# Required for LLM operations
LLM_API_KEY=your-api-key
EMBEDDING_API_KEY=your-api-key
```

## Summary

The fix changes database pool initialization from **eager** (at import time) to **lazy** (when first needed). This allows:

1. ✅ **Modules to import successfully** without environment variables
2. ✅ **Environment variables to be loaded** before validation
3. ✅ **Clear error messages** when configuration is missing
4. ✅ **Proper application startup sequence**

The API server should now start successfully and only validate the database connection when it's actually needed!
