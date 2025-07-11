# Web UI Setup Guide

## Quick Start

1. **Install dependencies:**
   ```bash
   cd web_ui
   pip install -r requirements.txt
   ```

2. **Start the web UI:**
   ```bash
   python start.py
   # or use the launcher script
   ./launch.sh
   ```

3. **Open your browser:**
   ```
   http://localhost:5000
   ```

## Prerequisites

- **Main API Server**: The Agentic RAG API must be running on port 8058
- **Python 3.8+**: Required for the web UI server
- **Modern Browser**: Chrome 80+, Firefox 75+, Safari 13+, or Edge 80+

## Starting the Main API Server

Before using the web UI, ensure the main Agentic RAG API is running:

```bash
# From the project root directory
source venv/bin/activate
python -m agent.api
```

The API should be accessible at: http://localhost:8058

## Web UI Components

### Files Created:
- `app.py` - Flask web server and API proxy
- `start.py` - Enhanced startup script with health checks
- `launch.sh` - Simple bash launcher
- `demo.py` - Testing and validation script
- `templates/index.html` - Main web interface
- `static/css/style.css` - Responsive styling
- `static/js/app.js` - Interactive JavaScript
- `requirements.txt` - Web UI dependencies
- `README.md` - Comprehensive documentation

### Features:
- ✅ Real-time streaming chat
- ✅ Session management
- ✅ Health status monitoring
- ✅ Tool usage display
- ✅ Document browser
- ✅ Chat export functionality
- ✅ Responsive mobile design
- ✅ Toast notifications
- ✅ Example queries

## Configuration

### Environment Variables:
```bash
export API_BASE_URL=http://localhost:8058  # Main API URL
export WEB_UI_PORT=5000                    # Web UI port
export WEB_UI_HOST=0.0.0.0                 # Web UI host
```

### Command Line Options:
```bash
python start.py --help
python start.py --api-url http://localhost:8058 --port 5000
python start.py --skip-health-check --debug
```

## Testing

Run the demo script to verify everything is working:

```bash
python demo.py
```

This will test:
- Dependencies installation
- Static files presence
- Web UI endpoints (if server is running)

## Troubleshooting

### Common Issues:

1. **"Connection Failed"**
   - Ensure the main API server is running on port 8058
   - Check the API_BASE_URL configuration
   - Verify network connectivity

2. **"Module not found" errors**
   - Install dependencies: `pip install -r requirements.txt`
   - Activate virtual environment: `source venv/bin/activate`

3. **"Port already in use"**
   - Change the port: `python start.py --port 5001`
   - Kill existing process: `lsof -ti:5000 | xargs kill`

4. **Streaming not working**
   - Check browser console for JavaScript errors
   - Ensure CORS is properly configured
   - Try refreshing the page

### Debug Mode:

```bash
python start.py --debug
```

### Logs:
Check the console output for detailed error messages and API communication logs.

## Architecture

```
Browser ↔ Flask Web UI (port 5000) ↔ Agentic RAG API (port 8058) ↔ AI Agent + Tools
```

The web UI acts as a proxy between the browser and the main API, providing:
- Static file serving
- API request forwarding
- Real-time streaming
- Error handling
- CORS support

## Next Steps

1. **Start the main API server**
2. **Install web UI dependencies**
3. **Launch the web UI**
4. **Open browser and start chatting!**

For detailed usage instructions, see the main README.md file.
