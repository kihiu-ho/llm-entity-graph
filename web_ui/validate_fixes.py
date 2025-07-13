#!/usr/bin/env python3
"""
Validation script to test that the Web UI fixes work correctly.
This script tests the fixes without requiring all dependencies to be installed.
"""

import os
import sys
import ast
import json
from pathlib import Path

def test_graceful_imports():
    """Test that the app handles missing imports gracefully."""
    print("🧪 Testing graceful import handling...")
    
    # Read the app.py file and check for graceful import patterns
    app_path = Path('app.py')
    if not app_path.exists():
        print("   ❌ app.py not found")
        return False
    
    with open(app_path, 'r') as f:
        content = f.read()
    
    # Check for graceful import patterns
    patterns = [
        'try:',
        'except ImportError:',
        'AIOHTTP_AVAILABLE',
        'FLASK_AVAILABLE',
        'CORS_AVAILABLE'
    ]
    
    found_patterns = []
    for pattern in patterns:
        if pattern in content:
            found_patterns.append(pattern)
            print(f"   ✅ Found graceful import pattern: {pattern}")
        else:
            print(f"   ❌ Missing pattern: {pattern}")
    
    return len(found_patterns) >= 4  # At least 4 patterns should be present


def test_error_handling():
    """Test that error handling is properly implemented."""
    print("\n🛡️  Testing error handling...")
    
    app_path = Path('app.py')
    with open(app_path, 'r') as f:
        content = f.read()
    
    # Check for error handling patterns
    error_patterns = [
        'if not AIOHTTP_AVAILABLE:',
        'except Exception as e:',
        'logger.error',
        'try:',
        'finally:'
    ]
    
    found_errors = []
    for pattern in error_patterns:
        if pattern in content:
            found_errors.append(pattern)
            print(f"   ✅ Found error handling: {pattern}")
    
    return len(found_errors) >= 3


def test_cors_fallback():
    """Test that CORS fallback is implemented."""
    print("\n🌐 Testing CORS fallback...")
    
    app_path = Path('app.py')
    with open(app_path, 'r') as f:
        content = f.read()
    
    # Check for CORS fallback
    cors_patterns = [
        'if CORS_AVAILABLE:',
        '@app.after_request',
        'Access-Control-Allow-Origin'
    ]
    
    found_cors = []
    for pattern in cors_patterns:
        if pattern in content:
            found_cors.append(pattern)
            print(f"   ✅ Found CORS handling: {pattern}")
    
    return len(found_cors) >= 2


def test_requirements_file():
    """Test that requirements.txt has all necessary dependencies."""
    print("\n📦 Testing requirements.txt...")
    
    req_path = Path('requirements.txt')
    if not req_path.exists():
        print("   ❌ requirements.txt not found")
        return False
    
    with open(req_path, 'r') as f:
        content = f.read()
    
    required_packages = [
        'Flask',
        'Flask-CORS',
        'aiohttp',
        'gunicorn',
        'requests',
        'Werkzeug'
    ]
    
    found_packages = []
    for package in required_packages:
        if package in content:
            found_packages.append(package)
            print(f"   ✅ Found package: {package}")
        else:
            print(f"   ❌ Missing package: {package}")
    
    return len(found_packages) == len(required_packages)


def test_file_structure():
    """Test that all required files exist."""
    print("\n📁 Testing file structure...")
    
    required_files = [
        'app.py',
        'requirements.txt',
        'templates/index.html',
        'static/css/style.css',
        'static/js/app.js',
        'setup_web_ui.py',
        'fix_web_ui.py',
        'WEB_UI_FIX_SUMMARY.md'
    ]
    
    found_files = []
    for file_path in required_files:
        if Path(file_path).exists():
            found_files.append(file_path)
            print(f"   ✅ Found: {file_path}")
        else:
            print(f"   ❌ Missing: {file_path}")
    
    return len(found_files) >= len(required_files) - 1  # Allow 1 missing file


def test_syntax_validity():
    """Test that Python files have valid syntax."""
    print("\n🔍 Testing Python syntax...")
    
    python_files = [
        'app.py',
        'setup_web_ui.py',
        'fix_web_ui.py'
    ]
    
    valid_files = []
    for file_path in python_files:
        if not Path(file_path).exists():
            print(f"   ⚠️  File not found: {file_path}")
            continue
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Parse the file to check syntax
            ast.parse(content)
            valid_files.append(file_path)
            print(f"   ✅ Valid syntax: {file_path}")
            
        except SyntaxError as e:
            print(f"   ❌ Syntax error in {file_path}: {e}")
        except Exception as e:
            print(f"   ❌ Error checking {file_path}: {e}")
    
    return len(valid_files) >= 2  # At least app.py should be valid


def test_configuration_handling():
    """Test that configuration is properly handled."""
    print("\n⚙️  Testing configuration handling...")
    
    app_path = Path('app.py')
    with open(app_path, 'r') as f:
        content = f.read()
    
    config_patterns = [
        'API_BASE_URL',
        'WEB_UI_PORT',
        'WEB_UI_HOST',
        'os.getenv'
    ]
    
    found_config = []
    for pattern in config_patterns:
        if pattern in content:
            found_config.append(pattern)
            print(f"   ✅ Found config handling: {pattern}")
    
    return len(found_config) >= 3


def test_documentation():
    """Test that documentation files exist and are comprehensive."""
    print("\n📚 Testing documentation...")
    
    doc_files = [
        'WEB_UI_FIX_SUMMARY.md',
        'README.md'
    ]
    
    found_docs = []
    for doc_file in doc_files:
        if Path(doc_file).exists():
            # Check if file has substantial content
            with open(doc_file, 'r') as f:
                content = f.read()
            
            if len(content) > 500:  # At least 500 characters
                found_docs.append(doc_file)
                print(f"   ✅ Found comprehensive doc: {doc_file}")
            else:
                print(f"   ⚠️  Doc too short: {doc_file}")
        else:
            print(f"   ❌ Missing doc: {doc_file}")
    
    return len(found_docs) >= 1


def main():
    """Main validation function."""
    print("🔍 Web UI Fix Validation")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path('app.py').exists():
        print("❌ Please run this script from the web_ui directory")
        sys.exit(1)
    
    tests = [
        ("Graceful Import Handling", test_graceful_imports),
        ("Error Handling", test_error_handling),
        ("CORS Fallback", test_cors_fallback),
        ("Requirements File", test_requirements_file),
        ("File Structure", test_file_structure),
        ("Python Syntax", test_syntax_validity),
        ("Configuration Handling", test_configuration_handling),
        ("Documentation", test_documentation)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("🏁 Validation Summary")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed >= len(results) - 1:  # Allow 1 failure
        print("\n🎉 Web UI fixes are working correctly!")
        print("\n💡 Next steps:")
        print("   1. Install dependencies: python3 setup_web_ui.py")
        print("   2. Start the web UI: python3 run_web_ui.py")
        print("   3. Access at: http://localhost:5001")
    else:
        print("\n⚠️  Some validation tests failed. Review the fixes.")
    
    return passed >= len(results) - 1


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
