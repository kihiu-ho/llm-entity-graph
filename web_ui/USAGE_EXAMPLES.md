# Web UI Usage Examples

## Starting the Web UI

### Method 1: Using the startup script
```bash
cd web_ui
python start.py
```

### Method 2: Using the launcher script
```bash
cd web_ui
./launch.sh
```

### Method 3: With custom configuration
```bash
cd web_ui
python start.py --api-url http://localhost:8058 --port 5000 --host 0.0.0.0
```

### Method 4: Skip health check (if API isn't running yet)
```bash
cd web_ui
python start.py --skip-health-check
```

### Method 5: Debug mode
```bash
cd web_ui
python start.py --debug
```

## Expected Output

When starting successfully, you should see:

```
============================================================
🌐 Agentic RAG Web UI Startup
============================================================
📡 API URL: http://localhost:8058
🚀 Web UI URL: http://0.0.0.0:5000
============================================================

🔍 Checking API health at http://localhost:8058
✅ API is healthy!

🎉 Web UI is ready!

📖 Quick Start Guide:
   1. Open your browser to the Web UI URL above
   2. Check the connection status in the header
   3. Try one of the example queries
   4. Use the sidebar for quick search and documents

💡 Tips:
   • Press Enter to send messages
   • Use Shift+Enter for new lines
   • Click example queries to try them
   • Export your conversations anytime

🛠️  Troubleshooting:
   • If connection fails, ensure the API server is running
   • Check the console for any error messages
   • Refresh the page if streaming stops working

============================================================
🚀 Starting Web UI server...
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
 * Running on http://[::1]:5000
```

## Using the Web Interface

### 1. Open your browser
Navigate to: http://localhost:5000

### 2. Check connection status
Look for the status indicator in the header:
- 🟢 Green dot = Connected and healthy
- 🟡 Yellow dot = Partially connected
- 🔴 Red dot = Disconnected

### 3. Start chatting
- Type your message in the text area at the bottom
- Press Enter to send (Shift+Enter for new lines)
- Watch the AI respond in real-time

### 4. Try example queries
Click on any of the suggested questions:
- "What are Google's AI initiatives?"
- "Tell me about Microsoft's partnerships with OpenAI"
- "Compare OpenAI and Anthropic's approaches to AI safety"

### 5. Browse documents
- Check the sidebar for available documents
- Click on documents to see details

### 6. Export conversations
- Click "Export Chat" in the sidebar
- Download your conversation as a text file

## Troubleshooting Common Issues

### Issue: "Connection Failed"
**Solution:**
1. Ensure the main API server is running:
   ```bash
   # From project root
   source venv/bin/activate
   python -m agent.api
   ```
2. Check the API URL in the web UI header
3. Verify the API is accessible at http://localhost:8058/health

### Issue: "Port already in use"
**Solution:**
```bash
# Use a different port
python start.py --port 5001

# Or kill the existing process
lsof -ti:5000 | xargs kill
```

### Issue: "Module not found"
**Solution:**
```bash
# Install dependencies
cd web_ui
pip install -r requirements.txt

# Or use virtual environment
source ../venv/bin/activate
pip install -r requirements.txt
```

### Issue: Streaming stops working
**Solution:**
1. Refresh the browser page
2. Check browser console for JavaScript errors
3. Restart the web UI server

### Issue: Search returns no results
**Solution:**
1. Ensure documents are ingested in the knowledge base
2. Try different search types (Vector/Graph/Hybrid)
3. Check the main API server logs

## Advanced Configuration

### Environment Variables
```bash
export API_BASE_URL=http://localhost:8058
export WEB_UI_PORT=5000
export WEB_UI_HOST=0.0.0.0
```

### Custom API URL
```bash
python start.py --api-url http://your-api-server:8058
```

### Production Deployment
```bash
# Use a production WSGI server
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## Testing the Setup

Run the test scripts to verify everything is working:

```bash
# Test dependencies and file structure
python demo.py

# Test startup without errors
python test_startup.py
```

Both should show all green checkmarks (✅) if everything is configured correctly.
