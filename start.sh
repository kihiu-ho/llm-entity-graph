#!/bin/bash
# Startup script for Agentic RAG with Web UI on Claw Run Cloud

set -e

echo "🚀 Starting Agentic RAG with Web UI..."
echo "=================================="

# Check if we're in production mode
PRODUCTION_MODE=${PRODUCTION_MODE:-"true"}
API_PORT=${APP_PORT:-8058}
WEB_UI_PORT=${WEB_UI_PORT:-5000}
APP_ENV=${APP_ENV:-"production"}

# Function to check if a service is running
check_service() {
    local port=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1
    
    echo "⏳ Waiting for $service_name to start on port $port..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "http://localhost:$port/health" > /dev/null 2>&1; then
            echo "✅ $service_name is ready!"
            return 0
        fi
        
        echo "   Attempt $attempt/$max_attempts - waiting..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "❌ $service_name failed to start after $max_attempts attempts"
    return 1
}

# Function to start the API server
start_api() {
    echo "🔧 Starting Agentic RAG API server..."

    # Set environment variables for the API server
    export APP_HOST=0.0.0.0
    export APP_PORT=$API_PORT
    export APP_ENV=${APP_ENV:-"production"}

    # Always use the agent.api module which has uvicorn built-in
    python -m agent.api &

    API_PID=$!
    echo "📝 API server started with PID: $API_PID"
}

# Function to start the web UI
start_webui() {
    echo "🌐 Starting Web UI server..."
    
    cd web_ui
    
    if [ "$PRODUCTION_MODE" = "true" ]; then
        # Production mode
        python start.py \
            --api-url "http://localhost:$API_PORT" \
            --host 0.0.0.0 \
            --port $WEB_UI_PORT \
            --production \
            --skip-health-check
    else
        # Development mode
        python start.py \
            --api-url "http://localhost:$API_PORT" \
            --host 0.0.0.0 \
            --port $WEB_UI_PORT \
            --skip-health-check
    fi
}

# Function to handle shutdown
cleanup() {
    echo "🛑 Shutting down services..."
    
    if [ ! -z "$API_PID" ]; then
        echo "   Stopping API server (PID: $API_PID)..."
        kill $API_PID 2>/dev/null || true
    fi
    
    # Kill any remaining processes
    pkill -f "python -m agent.api" 2>/dev/null || true
    pkill -f "python start.py" 2>/dev/null || true
    pkill -f "gunicorn" 2>/dev/null || true
    
    echo "✅ Cleanup complete"
    exit 0
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT

# Main execution
main() {
    echo "🔍 Environment check..."
    echo "   Production mode: $PRODUCTION_MODE"
    echo "   API port: $API_PORT"
    echo "   Web UI port: $WEB_UI_PORT"
    echo ""
    
    # Start API server
    start_api
    
    # Wait for API to be ready
    if ! check_service $API_PORT "API server"; then
        echo "❌ Failed to start API server"
        cleanup
        exit 1
    fi
    
    echo ""
    echo "🎉 API server is ready!"
    echo "   Health check: http://localhost:$API_PORT/health"
    echo ""
    
    # Start Web UI (this will run in foreground)
    start_webui
}

# Run main function
main
