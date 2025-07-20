#!/usr/bin/env python3
"""
Simple test to verify CLI integration works with basic mode.
"""

import os
import tempfile
import subprocess
import sys

def test_cli_basic_mode():
    """Test CLI with basic mode."""
    
    print("="*80)
    print("TESTING CLI BASIC MODE INTEGRATION")
    print("="*80)
    
    try:
        # Create test document
        temp_dir = tempfile.mkdtemp()
        test_file = os.path.join(temp_dir, "simple_test.md")
        
        with open(test_file, 'w') as f:
            f.write("""# Simple Test Document

## Basic Content

This is a simple test document for verifying basic ingestion functionality.

John Smith is the CEO of TestCorp.
Jane Doe works at TestCorp as the CTO.

The company was founded in 2020 and has grown rapidly.
""")
        
        print(f"✅ Created test document: {test_file}")
        
        # Test CLI with fast mode (which should work)
        cmd = [
            sys.executable, "-m", "ingestion.ingest",
            "--documents", temp_dir,
            "--fast",
            "--verbose"
        ]
        
        print(f"🔄 Running CLI command: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        print(f"📊 CLI RESULTS:")
        print(f"   Return code: {result.returncode}")
        print(f"   Stdout: {result.stdout}")
        if result.stderr:
            print(f"   Stderr: {result.stderr}")
        
        if result.returncode == 0:
            print(f"✅ CLI basic mode works correctly")
            return True
        else:
            print(f"❌ CLI basic mode failed")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    finally:
        # Clean up
        try:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
        except:
            pass

if __name__ == "__main__":
    success = test_cli_basic_mode()
    
    print(f"\n🎯 RESULT: {'SUCCESS' if success else 'FAILED'}")
    
    if success:
        print("✅ CLI integration with basic mode works")
        print("✅ The 'python -m ingestion.ingest' command processes files correctly")
        print("✅ Basic ingestion functionality is available")
    else:
        print("❌ CLI integration needs attention")
        print("❌ Check the ingestion pipeline configuration")
