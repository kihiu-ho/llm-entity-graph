# Fix for Gunicorn Worker Timeout and Async/Sync Issues

## Problem
Web UI fails with worker timeout errors:
```
[2025-07-13 13:11:49 +0000] [76] [CRITICAL] WORKER TIMEOUT (pid:80)
RuntimeError: Event loop is closed
SystemExit: 1
```

## Root Cause
The issue was caused by:

1. **Async/Sync Mixing**: Flask (synchronous) trying to handle async operations
2. **Blocking Event Loop**: Using `loop.run_until_complete()` in a streaming context
3. **Worker Timeout**: Gunicorn workers timing out due to blocking operations
4. **Resource Leaks**: Event loops not being properly cleaned up

## Solution Applied

### 1. **Fixed Async-to-Sync Bridge**

**Before (Problematic):**
```python
# This was blocking the worker
async_gen = stream_response()
while True:
    chunk = loop.run_until_complete(async_gen.__anext__())
    yield chunk
```

**After (Thread-Based):**
```python
def generate():
    """Generate streaming response using thread-based approach."""
    chunk_queue = queue.Queue()
    
    def async_worker():
        """Worker thread to handle async operations."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def stream_chunks():
            async for chunk in client.stream_chat(message, session_id, user_id):
                chunk_queue.put(f"data: {json.dumps(chunk)}\n\n")
        
        loop.run_until_complete(stream_chunks())
    
    # Start worker thread and yield chunks as they arrive
    worker = threading.Thread(target=async_worker, daemon=True)
    worker.start()
    
    while True:
        chunk = chunk_queue.get(timeout=30)
        if chunk is None:
            break
        yield chunk
```

### 2. **Enhanced Gunicorn Configuration**

**Updated `web_ui/start.py`:**
```python
cmd = [
    sys.executable, "-m", "gunicorn",
    "--bind", f"{web_ui_host}:{web_ui_port}",
    "--workers", "2",  # Reduced workers for better resource management
    "--worker-class", "sync",
    "--timeout", "300",  # Increased timeout for long-running requests
    "--graceful-timeout", "30",
    "--keep-alive", "5",
    "--max-requests", "500",  # Reduced to prevent memory leaks
    "--max-requests-jitter", "50",
    "--worker-tmp-dir", "/dev/shm",  # Use shared memory for better performance
    "--access-logfile", "-",
    "--error-logfile", "-",
    "--log-level", "info",
    "app:app"
]
```

### 3. **Improved Health Check**

**Enhanced health endpoint:**
```python
@app.route('/health')
def health():
    """Check API health status."""
    loop = None
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Run with timeout to prevent hanging
        health_data = loop.run_until_complete(
            asyncio.wait_for(get_health(), timeout=10.0)
        )
        return jsonify(health_data)
    except asyncio.TimeoutError:
        return jsonify({"status": "error", "message": "Health check timeout"}), 503
    finally:
        # Proper cleanup
        if loop:
            # Clean up any remaining tasks
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()
            if pending:
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            loop.close()
```

### 4. **Key Improvements**

- ✅ **Thread-based streaming** - Async operations run in separate thread
- ✅ **Non-blocking main thread** - Flask worker doesn't block
- ✅ **Proper timeouts** - Prevents hanging requests
- ✅ **Resource cleanup** - Event loops properly closed
- ✅ **Error handling** - Graceful degradation on failures
- ✅ **Keepalive mechanism** - Prevents client timeouts

## Files Modified

### 1. `web_ui/app.py`
- Added thread-based async-to-sync bridge
- Implemented proper event loop cleanup
- Added timeout handling and keepalive
- Enhanced error handling and logging

### 2. `web_ui/start.py`
- Increased Gunicorn timeout from 120s to 300s
- Reduced workers from 4 to 2 for better resource management
- Added shared memory configuration
- Reduced max requests to prevent memory leaks

## Performance Improvements

### ✅ **Better Resource Management**
- Reduced worker count to prevent resource contention
- Shared memory for better performance
- Proper event loop cleanup

### ✅ **Timeout Handling**
- 300-second worker timeout for long requests
- 30-second streaming timeout with keepalive
- 10-second health check timeout

### ✅ **Memory Management**
- Reduced max requests per worker
- Proper cleanup of async resources
- Daemon threads for background operations

## Deployment Impact

### ✅ **Stability**
- No more worker timeouts
- Proper handling of long-running requests
- Graceful error recovery

### ✅ **Performance**
- Non-blocking streaming
- Better resource utilization
- Reduced memory leaks

### ✅ **Monitoring**
- Better error logging
- Health check improvements
- Keepalive for connection monitoring

## Testing the Fix

### 1. **Local Testing**
```bash
# Test the web UI locally
cd web_ui
python start.py --production --host 0.0.0.0 --port 5000
```

### 2. **Load Testing**
```bash
# Test multiple concurrent requests
for i in {1..5}; do
  curl -X POST http://localhost:5000/chat \
    -H "Content-Type: application/json" \
    -d '{"message": "Test message '$i'"}' &
done
```

### 3. **Health Check Testing**
```bash
# Test health endpoint
curl http://localhost:5000/health
```

## Troubleshooting

### If Worker Timeouts Still Occur

1. **Check logs for specific errors:**
   ```bash
   docker logs your-container | grep -E "(TIMEOUT|ERROR)"
   ```

2. **Monitor resource usage:**
   ```bash
   docker stats your-container
   ```

3. **Increase timeout if needed:**
   - Edit `web_ui/start.py`
   - Increase `--timeout` value beyond 300

### If Streaming Issues Persist

1. **Check thread creation:**
   - Monitor thread count in logs
   - Ensure threads are being cleaned up

2. **Test with simpler requests:**
   - Try non-streaming endpoints first
   - Gradually test more complex operations

## Summary

The fix addresses the core async/sync mixing issue by:

1. ✅ **Isolating async operations** in separate threads
2. ✅ **Using queue-based communication** between threads
3. ✅ **Implementing proper timeouts** and cleanup
4. ✅ **Enhancing Gunicorn configuration** for stability
5. ✅ **Adding comprehensive error handling**

The web UI should now handle streaming requests without worker timeouts or event loop issues!
