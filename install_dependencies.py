#!/usr/bin/env python3
"""
Installation script to ensure all dependencies are properly installed.
This script checks for and installs missing dependencies, particularly tiktoken.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Command: {command}")
        print(f"   Error: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python {version.major}.{version.minor} is not supported. Please use Python 3.8 or higher.")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def check_virtual_environment():
    """Check if we're in a virtual environment."""
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    if in_venv:
        print("✅ Running in virtual environment")
    else:
        print("⚠️  Not running in virtual environment. Consider using a virtual environment.")
    return True

def install_requirements():
    """Install requirements from requirements.txt."""
    requirements_file = Path("requirements.txt")
    if not requirements_file.exists():
        print("❌ requirements.txt not found")
        return False
    
    return run_command("pip install -r requirements.txt", "Installing requirements from requirements.txt")

def install_tiktoken():
    """Specifically install tiktoken."""
    return run_command("pip install tiktoken==0.9.0", "Installing tiktoken")

def verify_tiktoken():
    """Verify that tiktoken is properly installed."""
    try:
        import tiktoken
        print("✅ tiktoken imported successfully")
        
        # Test basic functionality
        encoding = tiktoken.get_encoding("cl100k_base")
        test_text = "This is a test sentence."
        tokens = encoding.encode(test_text)
        decoded = encoding.decode(tokens)
        
        print(f"✅ tiktoken test: '{test_text}' -> {len(tokens)} tokens -> '{decoded}'")
        return True
    except ImportError as e:
        print(f"❌ Failed to import tiktoken: {e}")
        return False
    except Exception as e:
        print(f"❌ tiktoken test failed: {e}")
        return False

def verify_embedder():
    """Verify that the embedder works with tiktoken."""
    try:
        sys.path.append('.')
        from ingestion.embedder import EmbeddingGenerator
        
        embedder = EmbeddingGenerator()
        if embedder.tokenizer is not None:
            print("✅ EmbeddingGenerator initialized with tiktoken successfully")
            return True
        else:
            print("⚠️  EmbeddingGenerator initialized but tiktoken not available")
            return False
    except ImportError as e:
        print(f"❌ Failed to import EmbeddingGenerator: {e}")
        return False
    except Exception as e:
        print(f"❌ EmbeddingGenerator test failed: {e}")
        return False

def main():
    """Main installation and verification process."""
    print("🚀 Starting dependency installation and verification...")
    print("=" * 60)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Check virtual environment
    check_virtual_environment()
    
    # Install requirements
    if not install_requirements():
        print("\n⚠️  Failed to install requirements. Trying to install tiktoken specifically...")
        if not install_tiktoken():
            print("❌ Failed to install tiktoken. Please install manually:")
            print("   pip install tiktoken==0.9.0")
            sys.exit(1)
    
    print("\n🔍 Verifying installations...")
    print("-" * 40)
    
    # Verify tiktoken
    if not verify_tiktoken():
        print("❌ tiktoken verification failed. Trying to install it specifically...")
        if install_tiktoken() and verify_tiktoken():
            print("✅ tiktoken installed and verified successfully")
        else:
            print("❌ Failed to install or verify tiktoken")
            sys.exit(1)
    
    # Verify embedder integration
    if not verify_embedder():
        print("⚠️  EmbeddingGenerator verification failed, but tiktoken is available")
        print("   This might be due to missing other dependencies")
    
    print("\n" + "=" * 60)
    print("🎉 Installation and verification completed!")
    print("\nNext steps:")
    print("1. Make sure your .env file is configured with API keys")
    print("2. Test the embedding functionality:")
    print("   python -c \"from ingestion.embedder import EmbeddingGenerator; print('✅ Ready!')\"")
    print("3. Run document ingestion:")
    print("   python ingest_with_cleanup.py --documents documents")

if __name__ == "__main__":
    main()
