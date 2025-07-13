# Fix for Windows Line Endings Error

## Problem
Container fails with errors like:
```
/app/start.sh: line 3: $'\r': command not found
/app/start.sh: line 4: set: -: invalid option
/app/start.sh: line 16: syntax error near unexpected token `$'{\r''
```

## Root Cause
The startup scripts have **Windows line endings** (`\r\n`) instead of **Unix line endings** (`\n`). This happens when:
- Files are edited on Windows
- Git is configured to convert line endings
- Files are copied from Windows systems

## Solution Applied

### 1. Fixed Line Endings Locally
```bash
# Remove carriage returns from scripts
sed -i '' 's/\r$//' start.sh start_combined.sh
```

### 2. Updated Dockerfiles to Auto-Fix Line Endings

**Dockerfile (Fixed):**
```dockerfile
# Copy application code
COPY . .

# Fix line endings and ensure startup script exists and is executable
RUN sed -i 's/\r$//' /app/start.sh && \
    ls -la /app/start.sh && \
    chmod +x /app/start.sh

# Start both services using bash explicitly
CMD ["/bin/bash", "/app/start.sh"]
```

**Dockerfile.claw (Fixed):**
```dockerfile
# Copy application code
COPY . .

# Fix line endings and ensure startup script exists and is executable (before switching to non-root user)
RUN sed -i 's/\r$//' /app/start_combined.sh && \
    ls -la /app/start_combined.sh && \
    chmod +x /app/start_combined.sh

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app
RUN chown -R app:app /app
USER app

# Start command - Combined API + Web UI with proper process management
CMD ["/bin/bash", "/app/start_combined.sh"]
```

## Prevention Strategies

### 1. Git Configuration
Add to `.gitattributes` file:
```
*.sh text eol=lf
*.py text eol=lf
*.md text eol=lf
*.txt text eol=lf
```

### 2. Editor Configuration
**VS Code** - Add to settings.json:
```json
{
  "files.eol": "\n",
  "files.insertFinalNewline": true
}
```

**Vim** - Add to .vimrc:
```vim
set fileformat=unix
```

### 3. Git Global Settings
```bash
# Configure Git to handle line endings properly
git config --global core.autocrlf false
git config --global core.eol lf
```

## Verification Commands

### Check for Windows Line Endings
```bash
# Method 1: Using file command
file start.sh start_combined.sh

# Method 2: Using hexdump
hexdump -C start.sh | head -5

# Method 3: Using grep
grep -l $'\r' *.sh || echo "No carriage returns found"

# Method 4: Using od
od -c start.sh | head -5
```

### Fix Line Endings Manually
```bash
# Method 1: Using sed (macOS/Linux)
sed -i '' 's/\r$//' start.sh start_combined.sh

# Method 2: Using dos2unix (if available)
dos2unix start.sh start_combined.sh

# Method 3: Using tr
tr -d '\r' < start.sh > start_fixed.sh && mv start_fixed.sh start.sh
```

## Testing the Fix

### 1. Verify Scripts Locally
```bash
# Test script syntax
bash -n start.sh
bash -n start_combined.sh

# Test script execution (dry run)
bash start.sh --help 2>/dev/null || echo "Script syntax OK"
```

### 2. Test Docker Build
```bash
# Build with line ending fix
docker build -f Dockerfile.claw -t test-line-endings .

# Verify script in container
docker run --rm test-line-endings cat /app/start_combined.sh | head -5
```

### 3. Test Container Startup
```bash
# Test with minimal environment
docker run --rm \
  -e DATABASE_URL="test" \
  -e NEO4J_URI="test" \
  -e NEO4J_USERNAME="test" \
  -e NEO4J_PASSWORD="test" \
  -e LLM_API_KEY="test" \
  test-line-endings \
  /bin/bash -c "echo 'Testing script...' && head -5 /app/start_combined.sh"
```

## Complete Fix Summary

### What Was Fixed:
1. ✅ **Removed carriage returns** from startup scripts locally
2. ✅ **Added automatic line ending conversion** in Dockerfiles
3. ✅ **Maintained script permissions** and verification
4. ✅ **Used explicit bash execution** for robustness

### Docker Build Process Now:
1. Copies all files including scripts
2. **Automatically removes Windows line endings** with `sed -i 's/\r$//'`
3. Verifies script exists with `ls -la`
4. Sets executable permissions with `chmod +x`
5. Executes with explicit bash interpreter

### Benefits:
- ✅ **Works regardless of development platform** (Windows/Mac/Linux)
- ✅ **Automatically fixes line endings** during build
- ✅ **Prevents future line ending issues**
- ✅ **Maintains cross-platform compatibility**

## Deployment Instructions

### For Claw Cloud:
1. **Use the updated Dockerfile.claw** with line ending fixes
2. **Deploy from Git repository** (source build)
3. **Set environment variables** in claw.cloud console
4. **Monitor logs** for successful startup without `$'\r'` errors

### For Local Development:
1. **Configure Git** for proper line endings
2. **Set editor** to use Unix line endings
3. **Use the verification commands** to check scripts
4. **Test Docker build** before deploying

The container should now start successfully without any line ending errors!
