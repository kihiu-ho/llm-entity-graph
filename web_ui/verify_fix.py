#!/usr/bin/env python3
"""
Verification script to confirm all syntax errors are fixed.
"""

import sys
import os
import subprocess
from pathlib import Path

def test_python_syntax():
    """Test Python syntax for all files."""
    print("🐍 Testing Python syntax...")
    
    files_to_test = [
        "app.py",
        "start.py", 
        "demo.py",
        "test_startup.py"
    ]
    
    all_good = True
    for file_path in files_to_test:
        if Path(file_path).exists():
            try:
                # Test syntax by compiling
                with open(file_path, 'r') as f:
                    compile(f.read(), file_path, 'exec')
                print(f"   ✅ {file_path} - syntax OK")
            except SyntaxError as e:
                print(f"   ❌ {file_path} - syntax error: {e}")
                all_good = False
            except Exception as e:
                print(f"   ⚠️  {file_path} - other error: {e}")
        else:
            print(f"   ⚠️  {file_path} - file not found")
    
    return all_good

def test_imports():
    """Test that all modules can be imported."""
    print("\n📦 Testing imports...")
    
    modules_to_test = [
        ("app", "Flask app"),
        ("start", "Startup script")
    ]
    
    all_good = True
    for module_name, description in modules_to_test:
        try:
            __import__(module_name)
            print(f"   ✅ {description} - imports OK")
        except Exception as e:
            print(f"   ❌ {description} - import error: {e}")
            all_good = False
    
    return all_good

def test_launch_scripts():
    """Test that launch scripts work."""
    print("\n🚀 Testing launch scripts...")
    
    # Test Python script help
    try:
        result = subprocess.run([
            sys.executable, "start.py", "--help"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0 and "usage:" in result.stdout:
            print("   ✅ start.py --help works")
        else:
            print(f"   ❌ start.py --help failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"   ❌ start.py test failed: {e}")
        return False
    
    # Test bash script
    if Path("launch.sh").exists():
        try:
            result = subprocess.run([
                "./launch.sh", "--help"
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                print("   ✅ launch.sh --help works")
            else:
                print(f"   ❌ launch.sh --help failed: {result.stderr}")
                return False
        except Exception as e:
            print(f"   ❌ launch.sh test failed: {e}")
            return False
    
    return True

def main():
    """Run all verification tests."""
    print("🔧 Web UI Fix Verification")
    print("=" * 50)
    
    all_tests_passed = True
    
    # Test syntax
    if not test_python_syntax():
        all_tests_passed = False
    
    # Test imports
    if not test_imports():
        all_tests_passed = False
    
    # Test launch scripts
    if not test_launch_scripts():
        all_tests_passed = False
    
    print("\n" + "=" * 50)
    if all_tests_passed:
        print("🎉 ALL TESTS PASSED!")
        print("\n✅ Syntax errors are completely fixed")
        print("✅ All modules import successfully")
        print("✅ Launch scripts work correctly")
        print("\n🚀 The web UI is ready to use!")
        print("\nTo start:")
        print("   python start.py --skip-health-check")
        print("   # or")
        print("   ./launch.sh --skip-health-check")
        return 0
    else:
        print("❌ SOME TESTS FAILED!")
        print("Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
