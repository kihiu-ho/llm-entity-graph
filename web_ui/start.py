#!/usr/bin/env python3
"""
Startup script for the Agentic RAG Web UI.

This script provides a convenient way to start the web UI with proper configuration
and health checks.
"""

import os
import sys
import time
import asyncio
import aiohttp
import argparse
from pathlib import Path

# Add the web_ui directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app import app, API_BASE_URL, WEB_UI_PORT, WEB_UI_HOST

async def check_api_health(base_url: str, max_retries: int = 5, delay: float = 2.0) -> bool:
    """Check if the API is healthy with retries."""
    print(f"🔍 Checking API health at {base_url}")
    
    for attempt in range(max_retries):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{base_url}/health", timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        data = await response.json()
                        status = data.get('status', 'unknown')
                        
                        if status == 'healthy':
                            print(f"✅ API is healthy!")
                            return True
                        else:
                            print(f"⚠️  API status: {status}")
                            
        except Exception as e:
            print(f"❌ Attempt {attempt + 1}/{max_retries} failed: {e}")
            
        if attempt < max_retries - 1:
            print(f"⏳ Retrying in {delay} seconds...")
            await asyncio.sleep(delay)
    
    return False

def print_banner(api_url, web_host, web_port):
    """Print startup banner."""
    print("\n" + "=" * 60)
    print("🌐 Agentic RAG Web UI Startup")
    print("=" * 60)
    print(f"📡 API URL: {api_url}")
    print(f"🚀 Web UI URL: http://{web_host}:{web_port}")
    print("=" * 60 + "\n")

def print_startup_info():
    """Print helpful startup information."""
    print("\n" + "🎉 Web UI is ready!")
    print("\n📖 Quick Start Guide:")
    print("   1. Open your browser to the Web UI URL above")
    print("   2. Check the connection status in the header")
    print("   3. Try one of the example queries")
    print("   4. Use the sidebar for quick search and documents")
    print("\n💡 Tips:")
    print("   • Press Enter to send messages")
    print("   • Use Shift+Enter for new lines")
    print("   • Click example queries to try them")
    print("   • Export your conversations anytime")
    print("\n🛠️  Troubleshooting:")
    print("   • If connection fails, ensure the API server is running")
    print("   • Check the console for any error messages")
    print("   • Refresh the page if streaming stops working")
    print("\n" + "=" * 60)

async def main():
    """Main startup function."""
    parser = argparse.ArgumentParser(
        description="Start the Agentic RAG Web UI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--api-url',
        default=API_BASE_URL,
        help=f'API base URL (default: {API_BASE_URL})'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=WEB_UI_PORT,
        help=f'Web UI port (default: {WEB_UI_PORT})'
    )
    
    parser.add_argument(
        '--host',
        default=WEB_UI_HOST,
        help=f'Web UI host (default: {WEB_UI_HOST})'
    )
    
    parser.add_argument(
        '--skip-health-check',
        action='store_true',
        help='Skip API health check on startup'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Run in debug mode'
    )

    parser.add_argument(
        '--production',
        action='store_true',
        help='Run in production mode with gunicorn'
    )

    args = parser.parse_args()

    # Update configuration via environment variables
    api_base_url = args.api_url
    web_ui_port = args.port
    web_ui_host = args.host

    # Set environment variables for the Flask app
    os.environ['API_BASE_URL'] = api_base_url
    os.environ['WEB_UI_PORT'] = str(web_ui_port)
    os.environ['WEB_UI_HOST'] = web_ui_host
    
    print_banner(api_base_url, web_ui_host, web_ui_port)

    # Health check
    if not args.skip_health_check:
        api_healthy = await check_api_health(api_base_url)
        
        if not api_healthy:
            print("\n⚠️  Warning: API health check failed!")
            print("The web UI will still start, but you may experience connection issues.")
            print("Please ensure the Agentic RAG API server is running.\n")
            
            response = input("Continue anyway? (y/N): ").strip().lower()
            if response not in ['y', 'yes']:
                print("Startup cancelled.")
                return
        print()
    
    # Start the Flask app
    try:
        print("🚀 Starting Web UI server...")
        print_startup_info()

        if args.production:
            # Production mode with gunicorn
            import subprocess
            import sys

            print("🚀 Starting in production mode with gunicorn...")
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
            subprocess.run(cmd)
        else:
            # Development mode with Flask
            app.run(
                host=web_ui_host,
                port=web_ui_port,
                debug=args.debug,
                use_reloader=False  # Disable reloader to avoid double startup
            )
        
    except KeyboardInterrupt:
        print("\n\n👋 Web UI server stopped.")
    except Exception as e:
        print(f"\n❌ Failed to start Web UI server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Startup error: {e}")
        sys.exit(1)
