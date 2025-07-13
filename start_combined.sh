#!/bin/bash
# Combined startup script for API + Web UI deployment on Claw Cloud

set -e  # Exit on any error

echo "🚀 Starting Combined Agentic RAG API + Web UI"
echo "=============================================="

# Function to check if a port is available
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "Port $port is already in use"
        return 1
    fi
    return 0
}

# Function to wait for a service to be ready
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1
    
    echo "⏳ Waiting for $service_name to be ready at $url..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "$url" >/dev/null 2>&1; then
            echo "✅ $service_name is ready!"
            return 0
        fi
        
        echo "   Attempt $attempt/$max_attempts - $service_name not ready yet..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "❌ $service_name failed to start within $((max_attempts * 2)) seconds"
    return 1
}

# Function to cleanup background processes
cleanup() {
    echo "🛑 Shutting down services..."
    if [ ! -z "$API_PID" ]; then
        kill $API_PID 2>/dev/null || true
        echo "   Stopped API server (PID: $API_PID)"
    fi
    if [ ! -z "$WEBUI_PID" ]; then
        kill $WEBUI_PID 2>/dev/null || true
        echo "   Stopped Web UI server (PID: $WEBUI_PID)"
    fi
    exit 0
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT

# Set default values
API_HOST=${API_HOST:-"0.0.0.0"}
API_PORT=${API_PORT:-"8058"}
WEB_UI_HOST=${WEB_UI_HOST:-"0.0.0.0"}
WEB_UI_PORT=${WEB_UI_PORT:-"5000"}
API_BASE_URL=${API_BASE_URL:-"http://localhost:8058"}

echo "📋 Configuration:"
echo "   API Server: $API_HOST:$API_PORT"
echo "   Web UI: $WEB_UI_HOST:$WEB_UI_PORT"
echo "   API Base URL: $API_BASE_URL"
echo ""

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

echo "✅ Environment validation passed"
echo ""

# Check if ports are available
echo "🔍 Checking port availability..."
if ! check_port $API_PORT; then
    echo "❌ API port $API_PORT is not available"
    exit 1
fi

if ! check_port $WEB_UI_PORT; then
    echo "❌ Web UI port $WEB_UI_PORT is not available"
    exit 1
fi

echo "✅ Ports $API_PORT and $WEB_UI_PORT are available"
echo ""

# Start API server in background
echo "🚀 Starting API server..."
python -m agent.api --host $API_HOST --port $API_PORT &
API_PID=$!

echo "   API server started with PID: $API_PID"

# Wait for API server to be ready
if ! wait_for_service "http://localhost:$API_PORT/health" "API server"; then
    echo "❌ API server failed to start"
    cleanup
    exit 1
fi

# Start Web UI server in background
echo "🌐 Starting Web UI server..."
python web_ui/start.py \
    --host $WEB_UI_HOST \
    --port $WEB_UI_PORT \
    --api-url $API_BASE_URL \
    --skip-health-check \
    --production &
WEBUI_PID=$!

echo "   Web UI server started with PID: $WEBUI_PID"

# Wait for Web UI server to be ready
if ! wait_for_service "http://localhost:$WEB_UI_PORT/health" "Web UI server"; then
    echo "❌ Web UI server failed to start"
    cleanup
    exit 1
fi

echo ""
echo "🎉 Combined deployment started successfully!"
echo "=============================================="
echo "📡 API Server: http://$API_HOST:$API_PORT"
echo "🌐 Web UI: http://$WEB_UI_HOST:$WEB_UI_PORT"
echo "🔗 Health Checks:"
echo "   API: http://localhost:$API_PORT/health"
echo "   Web UI: http://localhost:$WEB_UI_PORT/health"
echo ""
echo "Press Ctrl+C to stop both services"

# Wait for either process to exit
wait $API_PID $WEBUI_PID

# If we get here, one of the processes has exited
echo "⚠️  One of the services has stopped unexpectedly"
cleanup
