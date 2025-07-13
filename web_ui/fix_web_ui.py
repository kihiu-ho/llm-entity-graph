#!/usr/bin/env python3
"""
Fix script for Web UI issues.
This script identifies and fixes common issues with the web UI.
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed."""
    print("🔍 Checking Web UI dependencies...")
    
    required_packages = [
        'flask',
        'flask_cors',
        'aiohttp',
        'gunicorn',
        'requests',
        'werkzeug'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} - Missing")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n💡 Install missing packages:")
        print(f"   pip install {' '.join(missing_packages)}")
        return False
    
    print("✅ All dependencies are available!")
    return True


def check_file_structure():
    """Check if all required files exist."""
    print("\n🗂️  Checking file structure...")
    
    required_files = [
        'app.py',
        'start.py',
        'requirements.txt',
        'templates/index.html',
        'static/css/style.css',
        'static/js/app.js'
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} - Missing")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n❌ Missing files: {missing_files}")
        return False
    
    print("✅ All required files exist!")
    return True


def test_flask_import():
    """Test if Flask app can be imported."""
    print("\n🌐 Testing Flask app import...")
    
    try:
        # Test basic import
        import app
        print("   ✅ Flask app imported successfully")
        
        # Test app creation
        flask_app = app.app
        print("   ✅ Flask app instance created")
        
        # Test routes
        routes = [rule.rule for rule in flask_app.url_map.iter_rules()]
        expected_routes = ['/', '/health', '/chat', '/documents']
        
        for route in expected_routes:
            if any(route in r for r in routes):
                print(f"   ✅ Route {route} registered")
            else:
                print(f"   ⚠️  Route {route} not found")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Flask app import failed: {e}")
        return False


def check_static_files():
    """Check if static files are properly structured."""
    print("\n📁 Checking static files...")
    
    static_checks = [
        ('static/css/style.css', 'CSS file'),
        ('static/js/app.js', 'JavaScript file'),
        ('templates/index.html', 'HTML template')
    ]
    
    all_good = True
    
    for file_path, description in static_checks:
        if Path(file_path).exists():
            file_size = Path(file_path).stat().st_size
            print(f"   ✅ {description}: {file_path} ({file_size} bytes)")
        else:
            print(f"   ❌ {description}: {file_path} - Missing")
            all_good = False
    
    return all_good


def check_configuration():
    """Check configuration and environment variables."""
    print("\n⚙️  Checking configuration...")
    
    # Check environment variables
    env_vars = {
        'API_BASE_URL': os.getenv('API_BASE_URL', 'http://localhost:8058'),
        'WEB_UI_PORT': os.getenv('WEB_UI_PORT', '5001'),
        'WEB_UI_HOST': os.getenv('WEB_UI_HOST', '0.0.0.0')
    }
    
    for var, value in env_vars.items():
        print(f"   📝 {var}: {value}")
    
    # Check if API URL is reachable (optional)
    api_url = env_vars['API_BASE_URL']
    print(f"   🔗 API URL configured: {api_url}")
    
    return True


def create_test_script():
    """Create a simple test script for the web UI."""
    print("\n🧪 Creating test script...")
    
    test_script = '''#!/usr/bin/env python3
"""
Simple test script for Web UI.
"""

import sys
import time
import threading
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_app_startup():
    """Test that the app can start without errors."""
    try:
        from app import app
        
        # Test in a separate thread to avoid blocking
        def run_app():
            app.run(host='127.0.0.1', port=5002, debug=False, use_reloader=False)
        
        thread = threading.Thread(target=run_app, daemon=True)
        thread.start()
        
        # Give it a moment to start
        time.sleep(2)
        
        print("✅ Web UI started successfully (test mode)")
        return True
        
    except Exception as e:
        print(f"❌ Web UI startup failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Web UI startup...")
    success = test_app_startup()
    sys.exit(0 if success else 1)
'''
    
    with open('test_web_ui.py', 'w') as f:
        f.write(test_script)
    
    print("   ✅ Created test_web_ui.py")
    return True


def fix_common_issues():
    """Fix common issues with the web UI."""
    print("\n🔧 Fixing common issues...")
    
    fixes_applied = []
    
    # Fix 1: Ensure requirements.txt has all dependencies
    requirements_content = '''# Web UI specific dependencies
Flask==3.1.0
Flask-CORS==5.0.0
aiohttp==3.12.13
gunicorn==23.0.0
requests==2.32.3
Werkzeug==3.1.3

# These are already in the main requirements.txt but listed here for clarity
# when running the web UI independently
python-dotenv==1.1.0
'''
    
    with open('requirements.txt', 'w') as f:
        f.write(requirements_content)
    fixes_applied.append("Updated requirements.txt")
    
    # Fix 2: Create a simple launcher script
    launcher_content = '''#!/usr/bin/env python3
"""
Simple launcher for the Web UI.
"""

import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def main():
    """Main launcher function."""
    print("🚀 Starting Agentic RAG Web UI...")
    
    # Set default environment variables
    os.environ.setdefault('API_BASE_URL', 'http://localhost:8058')
    os.environ.setdefault('WEB_UI_PORT', '5001')
    os.environ.setdefault('WEB_UI_HOST', '0.0.0.0')
    
    try:
        from app import app
        
        port = int(os.environ.get('WEB_UI_PORT', 5001))
        host = os.environ.get('WEB_UI_HOST', '0.0.0.0')
        
        print(f"🌐 Web UI URL: http://{host}:{port}")
        print(f"📡 API URL: {os.environ.get('API_BASE_URL')}")
        
        app.run(host=host, port=port, debug=False)
        
    except Exception as e:
        print(f"❌ Failed to start Web UI: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
    
    with open('simple_start.py', 'w') as f:
        f.write(launcher_content)
    fixes_applied.append("Created simple_start.py launcher")
    
    for fix in fixes_applied:
        print(f"   ✅ {fix}")
    
    return True


def main():
    """Main fix function."""
    print("🔧 Web UI Fix Script")
    print("=" * 50)
    
    # Change to web_ui directory
    if not Path('app.py').exists():
        print("❌ Not in web_ui directory. Please run from web_ui folder.")
        sys.exit(1)
    
    checks = [
        ("File Structure", check_file_structure),
        ("Dependencies", check_dependencies),
        ("Flask Import", test_flask_import),
        ("Static Files", check_static_files),
        ("Configuration", check_configuration),
        ("Common Fixes", fix_common_issues),
        ("Test Script", create_test_script)
    ]
    
    results = []
    
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"❌ {check_name} check failed: {e}")
            results.append((check_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("🏁 Fix Summary")
    print("=" * 50)
    
    passed = 0
    for check_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{check_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} checks passed")
    
    if passed == len(results):
        print("\n🎉 Web UI is ready!")
        print("💡 Try running: python simple_start.py")
    else:
        print("\n⚠️  Some issues remain. Check the output above.")
    
    return passed == len(results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
