#!/bin/bash
# Simple launcher script for the Agentic RAG Web UI

echo "🚀 Launching Agentic RAG Web UI..."
echo ""

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ Error: app.py not found. Please run this script from the web_ui directory."
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed or not in PATH."
    exit 1
fi

# Check if required packages are installed
echo "📦 Checking dependencies..."
python3 -c "import flask, aiohttp" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Some dependencies are missing. Installing..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install dependencies. Please install manually:"
        echo "   pip install -r requirements.txt"
        exit 1
    fi
fi

echo "✅ Dependencies OK"
echo ""

# Start the web UI
echo "🌐 Starting Web UI..."
python3 start.py "$@"
