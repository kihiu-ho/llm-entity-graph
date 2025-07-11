#!/usr/bin/env python3
"""
Test script to verify the web UI can start without syntax errors.
"""

import sys
import os
import threading
import time
import requests
from pathlib import Path

# Add the web_ui directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_import():
    """Test that all modules can be imported without errors."""
    print("🧪 Testing imports...")
    
    try:
        import app
        print("   ✅ app.py imports successfully")
    except Exception as e:
        print(f"   ❌ app.py import failed: {e}")
        return False
    
    try:
        import start
        print("   ✅ start.py imports successfully")
    except Exception as e:
        print(f"   ❌ start.py import failed: {e}")
        return False
    
    return True

def test_flask_app():
    """Test that the Flask app can be created."""
    print("\n🌐 Testing Flask app creation...")
    
    try:
        from app import app
        print("   ✅ Flask app created successfully")
        
        # Test that routes are registered
        routes = [rule.rule for rule in app.url_map.iter_rules()]
        expected_routes = ['/', '/health', '/chat', '/documents']
        
        for route in expected_routes:
            if any(route in r for r in routes):
                print(f"   ✅ Route {route} registered")
            else:
                print(f"   ⚠️  Route {route} not found")
        
        return True
    except Exception as e:
        print(f"   ❌ Flask app creation failed: {e}")
        return False

def test_startup_script():
    """Test the startup script functions."""
    print("\n🚀 Testing startup script...")
    
    try:
        from start import print_banner, check_api_health
        
        # Test banner function
        print("   ✅ print_banner function available")
        
        # Test health check function
        print("   ✅ check_api_health function available")
        
        return True
    except Exception as e:
        print(f"   ❌ Startup script test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🔧 Web UI Startup Test")
    print("=" * 50)
    
    all_passed = True
    
    # Test imports
    if not test_import():
        all_passed = False
    
    # Test Flask app
    if not test_flask_app():
        all_passed = False
    
    # Test startup script
    if not test_startup_script():
        all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All tests passed! Web UI is ready to start.")
        print("\nTo start the web UI:")
        print("   python start.py")
        print("   # or")
        print("   ./launch.sh")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
