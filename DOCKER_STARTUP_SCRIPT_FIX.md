# Fix for "exec /app/start.sh: no such file or directory" Error

## Problem
The Docker container fails to start with the error:
```
exec /app/start.sh: no such file or directory
```

## Root Cause
The issue occurs because:
1. The startup script permissions are set after switching to non-root user
2. The script path might not be correctly copied or accessible
3. Line ending issues (Windows vs Unix) in the script files

## Solution Applied

### 1. Fixed Dockerfile.claw
**Before:**
```dockerfile
# Copy application code
COPY . .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app
RUN chown -R app:app /app
USER app

# Make startup script executable
RUN chmod +x start_combined.sh
```

**After:**
```dockerfile
# Copy application code
COPY . .

# Make startup script executable (before switching to non-root user)
RUN chmod +x start_combined.sh

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app
RUN chown -R app:app /app
USER app
```

### 2. Fixed Dockerfile
**Before:**
```dockerfile
# Copy application code
COPY . .

# Copy and set up startup script
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh
```

**After:**
```dockerfile
# Copy application code
COPY . .

# Make startup script executable
RUN chmod +x /app/start.sh
```

## Key Changes

1. **Permission Setting Order**: Set script permissions BEFORE switching to non-root user
2. **Removed Duplicate Copy**: The `COPY . .` already copies all files including scripts
3. **Proper Path Reference**: Use relative paths consistently

## Verification Steps

### 1. Check Script Permissions Locally
```bash
ls -la start*.sh
```
Expected output:
```
-rwxr-xr-x start.sh
-rwxr-xr-x start_combined.sh
```

### 2. Test Docker Build
```bash
# Test Dockerfile.claw
docker build -f Dockerfile.claw -t test-claw .

# Test regular Dockerfile
docker build -f Dockerfile -t test-regular .
```

### 3. Test Container Startup
```bash
# Test with minimal environment
docker run --rm -e DATABASE_URL="test" -e NEO4J_URI="test" -e NEO4J_USERNAME="test" -e NEO4J_PASSWORD="test" -e LLM_API_KEY="test" test-claw
```

## Alternative Solutions

### Option 1: Use ENTRYPOINT with bash
If the issue persists, modify the Dockerfile:
```dockerfile
# Instead of CMD ["./start_combined.sh"]
ENTRYPOINT ["/bin/bash", "./start_combined.sh"]
```

### Option 2: Use Full Path
```dockerfile
CMD ["/app/start_combined.sh"]
```

### Option 3: Use Shell Form
```dockerfile
CMD ./start_combined.sh
```

## Line Ending Fix (if needed)

If you're developing on Windows, ensure Unix line endings:
```bash
# Convert line endings
sed -i 's/\r$//' start_combined.sh
sed -i 's/\r$//' start.sh
```

## Deployment Instructions

### For Claw Cloud

1. **Ensure your repository has the fixed Dockerfiles**
2. **Deploy using source build** (not pre-built image):
   ```json
   {
     "framework": "docker",
     "dockerfile": "Dockerfile.claw"
   }
   ```

3. **Set required environment variables** in claw.cloud console:
   ```
   DATABASE_URL=your-database-url
   NEO4J_URI=your-neo4j-uri
   NEO4J_USERNAME=neo4j
   NEO4J_PASSWORD=your-password
   LLM_API_KEY=your-api-key
   EMBEDDING_API_KEY=your-api-key
   WEB_UI_HOST=0.0.0.0
   WEB_UI_PORT=5000
   API_HOST=0.0.0.0
   API_PORT=8058
   API_BASE_URL=http://localhost:8058
   APP_ENV=production
   ```

### For Local Testing

1. **Build the image:**
   ```bash
   docker build -f Dockerfile.claw -t agentic-rag .
   ```

2. **Run with environment variables:**
   ```bash
   docker run -p 5000:5000 -p 8058:8058 \
     -e DATABASE_URL="your-db-url" \
     -e NEO4J_URI="your-neo4j-uri" \
     -e NEO4J_USERNAME="neo4j" \
     -e NEO4J_PASSWORD="your-password" \
     -e LLM_API_KEY="your-api-key" \
     agentic-rag
   ```

## Troubleshooting

### If the error persists:

1. **Check script exists in container:**
   ```bash
   docker run --rm -it test-claw ls -la /app/start_combined.sh
   ```

2. **Check script permissions:**
   ```bash
   docker run --rm -it test-claw stat /app/start_combined.sh
   ```

3. **Test script manually:**
   ```bash
   docker run --rm -it test-claw /bin/bash -c "cd /app && ./start_combined.sh"
   ```

4. **Check for line ending issues:**
   ```bash
   docker run --rm -it test-claw file /app/start_combined.sh
   ```

## Summary

The fix ensures that:
- ✅ Startup scripts have correct permissions
- ✅ Permissions are set before switching to non-root user
- ✅ Scripts are accessible in the container
- ✅ Proper path references are used
- ✅ Compatible with claw.cloud deployment

The container should now start successfully without the "no such file or directory" error.
