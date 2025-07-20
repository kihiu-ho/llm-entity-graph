#!/usr/bin/env python3
"""
Start the web UI for testing.
"""

import subprocess
import sys
import os
import time

def start_web_ui():
    """Start the web UI server."""
    
    print("="*80)
    print("STARTING WEB UI FOR TESTING")
    print("="*80)
    
    # Change to the project directory
    project_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_dir)
    
    print(f"Working directory: {project_dir}")
    
    # Start the web UI
    print("\n🚀 Starting web UI server...")
    print("   URL: http://localhost:8000")
    print("   Press Ctrl+C to stop")
    
    try:
        # Run the web UI
        subprocess.run([sys.executable, "web_ui/app.py"], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Web UI stopped by user")
    except Exception as e:
        print(f"❌ Failed to start web UI: {e}")

if __name__ == "__main__":
    start_web_ui()
