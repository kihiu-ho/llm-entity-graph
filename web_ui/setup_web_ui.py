#!/usr/bin/env python3
"""
Setup script for the Agentic RAG Web UI.
This script installs dependencies and sets up the web UI.
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def install_dependencies():
    """Install required dependencies."""
    print("📦 Installing Web UI dependencies...")
    
    # List of required packages
    packages = [
        "Flask==3.1.0",
        "Flask-CORS==5.0.0", 
        "aiohttp==3.12.13",
        "gunicorn==23.0.0",
        "requests==2.32.3",
        "Werkzeug==3.1.3",
        "python-dotenv==1.1.0"
    ]
    
    try:
        # Install packages
        cmd = [sys.executable, "-m", "pip", "install"] + packages
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Dependencies installed successfully!")
            return True
        else:
            print(f"❌ Failed to install dependencies: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Installation error: {e}")
        return False


def check_installation():
    """Check if all dependencies are properly installed."""
    print("\n🔍 Checking installation...")
    
    required_modules = [
        ('flask', 'Flask'),
        ('flask_cors', 'Flask-CORS'),
        ('aiohttp', 'aiohttp'),
        ('requests', 'requests'),
        ('werkzeug', 'Werkzeug')
    ]
    
    all_good = True
    
    for module_name, package_name in required_modules:
        try:
            __import__(module_name)
            print(f"   ✅ {package_name}")
        except ImportError:
            print(f"   ❌ {package_name} - Not available")
            all_good = False
    
    return all_good


def test_web_ui():
    """Test that the web UI can start."""
    print("\n🧪 Testing Web UI...")
    
    try:
        # Test import
        from app import app
        print("   ✅ Flask app imported successfully")
        
        # Test routes
        with app.test_client() as client:
            # Test main page
            response = client.get('/')
            if response.status_code == 200:
                print("   ✅ Main page accessible")
            else:
                print(f"   ⚠️  Main page returned {response.status_code}")
            
            # Test health endpoint
            response = client.get('/health')
            if response.status_code == 200:
                print("   ✅ Health endpoint accessible")
            else:
                print(f"   ⚠️  Health endpoint returned {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Web UI test failed: {e}")
        return False


def create_env_file():
    """Create a sample .env file for configuration."""
    print("\n📝 Creating sample .env file...")
    
    env_content = """# Agentic RAG Web UI Configuration

# API Configuration
API_BASE_URL=http://localhost:8058

# Web UI Configuration  
WEB_UI_HOST=0.0.0.0
WEB_UI_PORT=5001

# Optional: Enable debug mode (development only)
# FLASK_DEBUG=true
"""
    
    env_path = Path('.env.example')
    
    try:
        with open(env_path, 'w') as f:
            f.write(env_content)
        print(f"   ✅ Created {env_path}")
        
        if not Path('.env').exists():
            # Copy to .env if it doesn't exist
            with open('.env', 'w') as f:
                f.write(env_content)
            print("   ✅ Created .env file")
        else:
            print("   ℹ️  .env file already exists")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Failed to create .env file: {e}")
        return False


def create_startup_scripts():
    """Create convenient startup scripts."""
    print("\n🚀 Creating startup scripts...")
    
    # Simple Python launcher
    python_launcher = '''#!/usr/bin/env python3
"""
Simple launcher for the Agentic RAG Web UI.
"""

import os
import sys
from pathlib import Path

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

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
        debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
        
        print(f"🌐 Web UI URL: http://{host}:{port}")
        print(f"📡 API URL: {os.environ.get('API_BASE_URL')}")
        print(f"🔧 Debug mode: {debug}")
        print()
        print("Press Ctrl+C to stop the server")
        
        app.run(host=host, port=port, debug=debug)
        
    except KeyboardInterrupt:
        print("\\n👋 Web UI stopped")
    except Exception as e:
        print(f"❌ Failed to start Web UI: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
    
    # Bash launcher
    bash_launcher = '''#!/bin/bash
# Bash launcher for the Agentic RAG Web UI

echo "🚀 Starting Agentic RAG Web UI..."

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ Please run this script from the web_ui directory"
    exit 1
fi

# Load environment variables if .env exists
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Set defaults
export API_BASE_URL=${API_BASE_URL:-"http://localhost:8058"}
export WEB_UI_PORT=${WEB_UI_PORT:-"5001"}
export WEB_UI_HOST=${WEB_UI_HOST:-"0.0.0.0"}

echo "🌐 Web UI URL: http://$WEB_UI_HOST:$WEB_UI_PORT"
echo "📡 API URL: $API_BASE_URL"
echo ""
echo "Press Ctrl+C to stop the server"

# Start the web UI
python3 run_web_ui.py
'''
    
    scripts_created = []
    
    try:
        # Create Python launcher
        with open('run_web_ui.py', 'w') as f:
            f.write(python_launcher)
        os.chmod('run_web_ui.py', 0o755)
        scripts_created.append('run_web_ui.py')
        
        # Create bash launcher
        with open('start_web_ui.sh', 'w') as f:
            f.write(bash_launcher)
        os.chmod('start_web_ui.sh', 0o755)
        scripts_created.append('start_web_ui.sh')
        
        for script in scripts_created:
            print(f"   ✅ Created {script}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Failed to create startup scripts: {e}")
        return False


def main():
    """Main setup function."""
    print("🔧 Agentic RAG Web UI Setup")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path('app.py').exists():
        print("❌ Please run this script from the web_ui directory")
        sys.exit(1)
    
    setup_steps = [
        ("Install Dependencies", install_dependencies),
        ("Check Installation", check_installation),
        ("Test Web UI", test_web_ui),
        ("Create Environment File", create_env_file),
        ("Create Startup Scripts", create_startup_scripts)
    ]
    
    results = []
    
    for step_name, step_func in setup_steps:
        try:
            result = step_func()
            results.append((step_name, result))
        except Exception as e:
            print(f"❌ {step_name} failed: {e}")
            results.append((step_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("🏁 Setup Summary")
    print("=" * 50)
    
    passed = 0
    for step_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{step_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} steps completed")
    
    if passed == len(results):
        print("\n🎉 Web UI setup complete!")
        print("\n💡 To start the Web UI:")
        print("   python3 run_web_ui.py")
        print("   # or")
        print("   ./start_web_ui.sh")
        print("\n🌐 The Web UI will be available at: http://localhost:5001")
    else:
        print("\n⚠️  Some setup steps failed. Check the output above.")
    
    return passed == len(results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
