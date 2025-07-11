#!/usr/bin/env python3
"""
Demo script to test the Web UI functionality.

This script can be used to verify that all components are working correctly.
"""

import asyncio
import aiohttp
import json
import sys
from datetime import datetime

async def test_web_ui_endpoints():
    """Test the web UI endpoints."""
    base_url = "http://localhost:5000"
    
    print("🧪 Testing Web UI Endpoints")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        # Test health endpoint
        print("1. Testing health endpoint...")
        try:
            async with session.get(f"{base_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ Health check: {data.get('status', 'unknown')}")
                else:
                    print(f"   ❌ Health check failed: HTTP {response.status}")
        except Exception as e:
            print(f"   ❌ Health check error: {e}")
        
        # Test documents endpoint
        print("\n2. Testing documents endpoint...")
        try:
            async with session.get(f"{base_url}/documents") as response:
                if response.status == 200:
                    data = await response.json()
                    doc_count = len(data.get('documents', []))
                    print(f"   ✅ Documents endpoint: {doc_count} documents found")
                else:
                    print(f"   ❌ Documents endpoint failed: HTTP {response.status}")
        except Exception as e:
            print(f"   ❌ Documents endpoint error: {e}")


def test_static_files():
    """Test that static files exist."""
    import os
    from pathlib import Path
    
    print("\n🗂️  Testing Static Files")
    print("=" * 50)
    
    web_ui_dir = Path(__file__).parent
    static_files = [
        "templates/index.html",
        "static/css/style.css",
        "static/js/app.js"
    ]
    
    for file_path in static_files:
        full_path = web_ui_dir / file_path
        if full_path.exists():
            size = full_path.stat().st_size
            print(f"   ✅ {file_path} ({size:,} bytes)")
        else:
            print(f"   ❌ {file_path} (missing)")

def test_dependencies():
    """Test that required dependencies are available."""
    print("\n📦 Testing Dependencies")
    print("=" * 50)
    
    dependencies = [
        ("flask", "Flask"),
        ("flask_cors", "Flask-CORS"),
        ("aiohttp", "aiohttp"),
        ("asyncio", "asyncio")
    ]
    
    for module_name, display_name in dependencies:
        try:
            __import__(module_name)
            print(f"   ✅ {display_name}")
        except ImportError:
            print(f"   ❌ {display_name} (not installed)")

async def main():
    """Main demo function."""
    print("🌐 Agentic RAG Web UI Demo")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test dependencies first
    test_dependencies()
    
    # Test static files
    test_static_files()
    
    # Test web UI endpoints (only if server is running)
    print("\n🔗 Testing Web UI Server")
    print("=" * 50)
    print("Note: This requires the web UI server to be running on localhost:5000")
    
    try:
        await test_web_ui_endpoints()
    except Exception as e:
        print(f"❌ Server test failed: {e}")
        print("💡 Start the web UI server first: python start.py")
    
    print("\n" + "=" * 50)
    print("🎯 Demo Complete!")
    print("\nTo start the web UI:")
    print("   python start.py")
    print("   # or")
    print("   ./launch.sh")
    print("\nThen open: http://localhost:5000")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Demo cancelled.")
    except Exception as e:
        print(f"❌ Demo error: {e}")
        sys.exit(1)
