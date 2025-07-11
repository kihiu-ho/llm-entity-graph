#!/bin/bash
# Development startup script for local testing
# This script starts only the web UI and assumes the API is running separately

set -e

echo "🚀 Starting Web UI for Development"
echo "================================="

# Configuration
WEB_UI_PORT=${WEB_UI_PORT:-5000}
API_URL=${API_URL:-"http://localhost:8058"}

# Function to check if API is running
check_api() {
    echo "🔍 Checking if API server is running..."
    
    # Try to connect to the API port
    if command -v curl >/dev/null 2>&1; then
        if curl -s -f "$API_URL/health" >/dev/null 2>&1; then
            echo "   ✅ API server is running at $API_URL"
            return 0
        fi
    elif command -v nc >/dev/null 2>&1; then
        # Extract host and port from URL
        host=$(echo "$API_URL" | sed 's|http://||' | cut -d: -f1)
        port=$(echo "$API_URL" | sed 's|http://||' | cut -d: -f2 | cut -d/ -f1)
        
        if nc -z "$host" "$port" 2>/dev/null; then
            echo "   ✅ API server is running at $API_URL"
            return 0
        fi
    fi
    
    echo "   ❌ API server not accessible at $API_URL"
    echo ""
    echo "📋 To start the API server:"
    echo "   1. Install dependencies: pip install -r requirements.txt"
    echo "   2. Start API server: python -m agent.api"
    echo "   3. Or use the full startup script: ./start.sh"
    echo ""
    
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Startup cancelled."
        exit 1
    fi
}

# Function to start web UI
start_webui() {
    echo "🌐 Starting Web UI..."
    echo "   Port: $WEB_UI_PORT"
    echo "   API URL: $API_URL"
    echo ""
    
    cd web_ui
    
    # Check if dependencies are installed
    if ! python3 -c "import flask" 2>/dev/null; then
        echo "⚠️  Web UI dependencies not installed. Installing..."
        pip3 install -r requirements.txt
    fi
    
    # Start the web UI
    python3 start.py \
        --api-url "$API_URL" \
        --host 0.0.0.0 \
        --port "$WEB_UI_PORT" \
        --skip-health-check
}

# Main execution
main() {
    echo "🔍 Environment check..."
    echo "   Web UI port: $WEB_UI_PORT"
    echo "   API URL: $API_URL"
    echo ""
    
    # Check API availability
    check_api
    
    echo ""
    echo "🎉 Starting Web UI..."
    echo "   Open your browser to: http://localhost:$WEB_UI_PORT"
    echo ""
    
    # Start Web UI
    start_webui
}

# Handle Ctrl+C
trap 'echo -e "\n🛑 Shutting down..."; exit 0' SIGINT SIGTERM

# Run main function
main
