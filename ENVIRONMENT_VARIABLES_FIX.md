# Fix for Environment Variables Not Loading in Container

## Problem
API server fails to start with error:
```
ValueError: DATABASE_URL environment variable not set
```

Even though we implemented lazy initialization, the environment variables aren't being loaded properly in the Docker container during startup.

## Root Causes

1. **Environment variables not passed to container** - Docker container doesn't have access to environment variables
2. **`.env` file not loaded properly** - The `.env` file exists but isn't being loaded before API startup
3. **Startup sequence issue** - API tries to initialize before environment variables are available

## Solution Applied

### 1. **Enhanced Environment Variable Loading**

**Updated `start_combined.sh`:**
```bash
# Load .env file if it exists and export variables
if [ -f "/app/.env" ]; then
    echo "🔧 Loading environment variables from .env file..."
    export $(grep -v '^#' /app/.env | grep -v '^$' | xargs)
fi

# Validate environment variables using Python script
echo "🔍 Validating environment variables..."
if ! python validate_environment.py; then
    echo "❌ Environment validation failed"
    exit 1
fi
```

### 2. **Improved API Startup Validation**

**Updated `agent/api.py`:**
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI app."""
    # Startup
    logger.info("Starting up agentic RAG API...")
    
    try:
        # Load environment variables explicitly
        from dotenv import load_dotenv
        load_dotenv()
        
        # Check required environment variables
        required_vars = ["DATABASE_URL", "NEO4J_URI", "NEO4J_USERNAME", "NEO4J_PASSWORD", "LLM_API_KEY"]
        missing_vars = []
        
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            logger.error(f"Missing required environment variables: {missing_vars}")
            raise ValueError(f"Missing required environment variables: {missing_vars}")
        
        logger.info("Environment variables validated")
        
        # Initialize database connections
        await initialize_database()
        # ... rest of startup
```

### 3. **Created Environment Validation Script**

**New `validate_environment.py`:**
- Validates all required environment variables
- Provides clear error messages for missing variables
- Masks sensitive values in output
- Returns proper exit codes for automation

### 4. **Key Improvements**

- ✅ **Explicit .env file loading** - Loads and exports variables before API startup
- ✅ **Comprehensive validation** - Checks all required variables with clear messages
- ✅ **Better error handling** - Fails fast with helpful error messages
- ✅ **Security conscious** - Masks sensitive values in logs
- ✅ **Automation friendly** - Proper exit codes for CI/CD

## Files Modified

### 1. `start_combined.sh`
- Added explicit `.env` file loading and export
- Integrated environment validation script
- Improved error handling and messaging

### 2. `agent/api.py`
- Added explicit `load_dotenv()` call during startup
- Enhanced environment variable validation
- Better error messages for missing variables

### 3. `validate_environment.py` (New)
- Comprehensive environment variable validation
- Clear output with masked sensitive values
- Proper exit codes for automation

## Environment Variables Required

### Required Variables
```bash
# Database Configuration
DATABASE_URL=postgresql://user:password@host:port/database

# Neo4j Configuration
NEO4J_URI=neo4j+s://instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password

# LLM Configuration
LLM_API_KEY=your-api-key
EMBEDDING_API_KEY=your-api-key
```

### Optional Variables
```bash
# LLM Configuration
LLM_PROVIDER=openai
LLM_CHOICE=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small
LLM_BASE_URL=https://api.openai.com/v1
EMBEDDING_BASE_URL=https://api.openai.com/v1

# Application Configuration
APP_ENV=production
LOG_LEVEL=INFO
```

## Deployment Instructions

### For Claw Cloud

1. **Set Environment Variables in Console:**
   - Go to your app settings in claw.cloud console
   - Add all required environment variables
   - Use the values from your `.env.claw` file

2. **Deploy with Updated Code:**
   - Use the updated startup scripts
   - Environment variables will be validated before startup
   - Clear error messages if any are missing

### For Local Testing

1. **Test Environment Validation:**
   ```bash
   python validate_environment.py
   ```

2. **Test Docker Build:**
   ```bash
   docker build -f Dockerfile.claw -t test-env .
   ```

3. **Test Container with Environment:**
   ```bash
   docker run -p 5000:5000 -p 8058:8058 \
     -e DATABASE_URL="your-db-url" \
     -e NEO4J_URI="your-neo4j-uri" \
     -e NEO4J_USERNAME="neo4j" \
     -e NEO4J_PASSWORD="your-password" \
     -e LLM_API_KEY="your-api-key" \
     -e EMBEDDING_API_KEY="your-api-key" \
     test-env
   ```

## Troubleshooting

### If Environment Variables Still Not Found

1. **Check Container Environment:**
   ```bash
   docker run --rm test-env env | grep -E "(DATABASE_URL|NEO4J|LLM_API_KEY)"
   ```

2. **Check .env File in Container:**
   ```bash
   docker run --rm test-env cat /app/.env
   ```

3. **Test Validation Script:**
   ```bash
   docker run --rm test-env python validate_environment.py
   ```

### For Claw Cloud Deployment

1. **Verify Environment Variables in Console:**
   - Check that all required variables are set
   - Ensure no typos in variable names
   - Verify values are correct (no extra spaces, etc.)

2. **Check Deployment Logs:**
   - Look for environment validation messages
   - Check for specific missing variables
   - Verify startup sequence

## Summary

The fix ensures that:

1. ✅ **Environment variables are loaded** before API startup
2. ✅ **Comprehensive validation** with clear error messages
3. ✅ **Proper startup sequence** - validate first, then initialize
4. ✅ **Better debugging** - clear messages about what's missing
5. ✅ **Security conscious** - sensitive values are masked in logs

The API server should now start successfully with proper environment variable loading and validation!
