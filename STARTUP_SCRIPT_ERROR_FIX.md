# Complete Fix for "exec /app/start.sh: no such file or directory"

## Problem
Docker container fails with:
```
exec /app/start.sh: no such file or directory
```

## Root Causes & Solutions

### 1. Script Not Found
**Cause**: The startup script isn't copied to the container or is in wrong location.

**Solution Applied**: 
- Removed redundant `COPY start.sh /app/start.sh` 
- Use `COPY . .` which copies all files including scripts
- Added verification step: `RUN ls -la /app/start.sh`

### 2. Permission Issues
**Cause**: Script doesn't have execute permissions.

**Solution Applied**:
- Set permissions explicitly: `RUN chmod +x /app/start.sh`
- For Dockerfile.claw: Set permissions before switching to non-root user

### 3. Execution Method
**Cause**: Direct script execution might fail due to shebang or interpreter issues.

**Solution Applied**:
- Use explicit bash interpreter: `CMD ["/bin/bash", "/app/start.sh"]`
- This works even if shebang is missing or incorrect

## Fixed Dockerfiles

### Dockerfile (Fixed)
```dockerfile
# Copy application code
COPY . .

# Ensure startup script exists and is executable
RUN ls -la /app/start.sh && chmod +x /app/start.sh

# Expose ports
EXPOSE 5000 8058

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Start both services using bash explicitly
CMD ["/bin/bash", "/app/start.sh"]
```

### Dockerfile.claw (Fixed)
```dockerfile
# Copy application code
COPY . .

# Ensure startup script exists and is executable (before switching to non-root user)
RUN ls -la /app/start_combined.sh && chmod +x /app/start_combined.sh

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app
RUN chown -R app:app /app
USER app

# Expose ports (Web UI on 5000, API on 8058)
EXPOSE 5000 8058

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Start command - Combined API + Web UI with proper process management
CMD ["/bin/bash", "/app/start_combined.sh"]
```

## Key Changes Made

1. **Removed Redundant Copy**: Eliminated `COPY start.sh /app/start.sh` since `COPY . .` handles this
2. **Added Verification**: `RUN ls -la /app/start.sh` to verify script exists during build
3. **Explicit Bash Execution**: `CMD ["/bin/bash", "/app/start.sh"]` instead of direct execution
4. **Permission Order**: Set permissions before user switch in Dockerfile.claw

## Testing the Fix

### Quick Test
```bash
# Test if script exists and is executable
ls -la start.sh start_combined.sh

# Should show:
# -rwxr-xr-x start.sh
# -rwxr-xr-x start_combined.sh
```

### Docker Build Test
```bash
# Test Dockerfile.claw build
docker build -f Dockerfile.claw -t test-fix .

# Test regular Dockerfile build  
docker build -f Dockerfile -t test-fix-regular .
```

### Container Test
```bash
# Test script accessibility in container
docker run --rm test-fix ls -la /app/start_combined.sh

# Test script execution (dry run)
docker run --rm test-fix /bin/bash -c "echo 'Testing script...' && ls -la /app/start_combined.sh"
```

## Alternative Solutions (if issue persists)

### Option 1: Use ENTRYPOINT
```dockerfile
ENTRYPOINT ["/bin/bash"]
CMD ["/app/start_combined.sh"]
```

### Option 2: Use Shell Form
```dockerfile
CMD /bin/bash /app/start_combined.sh
```

### Option 3: Create Wrapper Script
```dockerfile
RUN echo '#!/bin/bash' > /app/wrapper.sh && \
    echo 'exec /app/start_combined.sh "$@"' >> /app/wrapper.sh && \
    chmod +x /app/wrapper.sh
CMD ["/app/wrapper.sh"]
```

### Option 4: Fix Line Endings (if on Windows)
```bash
# Convert Windows line endings to Unix
sed -i 's/\r$//' start.sh
sed -i 's/\r$//' start_combined.sh
```

## Deployment Instructions

### For Claw Cloud

1. **Use the fixed Dockerfile.claw**
2. **Deploy from source** (not pre-built image):
   ```json
   {
     "framework": "docker",
     "dockerfile": "Dockerfile.claw",
     "build": {
       "context": ".",
       "dockerfile": "Dockerfile.claw"
     }
   }
   ```

3. **Set environment variables** in claw.cloud console:
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
   LOG_LEVEL=INFO
   ```

### For Local Testing

```bash
# Build with fixed Dockerfile
docker build -f Dockerfile.claw -t agentic-rag-fixed .

# Run with environment variables
docker run -p 5000:5000 -p 8058:8058 \
  -e DATABASE_URL="your-db-url" \
  -e NEO4J_URI="your-neo4j-uri" \
  -e NEO4J_USERNAME="neo4j" \
  -e NEO4J_PASSWORD="your-password" \
  -e LLM_API_KEY="your-api-key" \
  agentic-rag-fixed
```

## Troubleshooting

If the error still occurs:

1. **Check script exists locally**:
   ```bash
   ls -la start*.sh
   ```

2. **Verify script content**:
   ```bash
   head -5 start_combined.sh
   # Should start with #!/bin/bash
   ```

3. **Check for hidden characters**:
   ```bash
   cat -A start_combined.sh | head -5
   ```

4. **Test script manually**:
   ```bash
   bash start_combined.sh --help
   ```

5. **Check Docker build logs**:
   ```bash
   docker build -f Dockerfile.claw -t debug-build . --no-cache
   ```

## Summary

The fix ensures:
- ✅ Startup scripts are properly copied to container
- ✅ Scripts have correct execute permissions
- ✅ Permissions are set before user switch (for Dockerfile.claw)
- ✅ Scripts are executed with explicit bash interpreter
- ✅ Build process verifies script existence
- ✅ Compatible with claw.cloud deployment

This comprehensive fix should resolve the startup script error completely.
