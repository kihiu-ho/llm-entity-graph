#!/usr/bin/env python3
"""
Check for missing dependencies and provide installation instructions.
"""

import sys
import importlib
import subprocess

def check_dependency(module_name, package_name=None):
    """Check if a dependency is available."""
    if package_name is None:
        package_name = module_name
    
    try:
        importlib.import_module(module_name)
        print(f"✅ {module_name} - Available")
        return True
    except ImportError:
        print(f"❌ {module_name} - Missing (install with: pip install {package_name})")
        return False

def main():
    """Check all required dependencies."""
    print("🔍 Checking Dependencies for LLM Entity Graph")
    print("=" * 50)
    
    # Core dependencies
    dependencies = [
        ("pydantic", "pydantic"),
        ("asyncpg", "asyncpg"),
        ("openai", "openai"),
        ("neo4j", "neo4j"),
        ("graphiti_core", "graphiti-core"),
        ("numpy", "numpy"),
        ("pandas", "pandas"),
        ("tiktoken", "tiktoken"),
        ("python_dotenv", "python-dotenv"),
        ("pydantic_ai", "pydantic-ai"),
        ("asyncio", None),  # Built-in
        ("logging", None),  # Built-in
        ("json", None),     # Built-in
        ("re", None),       # Built-in
        ("os", None),       # Built-in
        ("sys", None),      # Built-in
    ]
    
    missing = []
    available = []
    
    for module, package in dependencies:
        if package is None:
            # Built-in module
            print(f"✅ {module} - Built-in")
            available.append(module)
        else:
            if check_dependency(module, package):
                available.append(module)
            else:
                missing.append(package)
    
    print("\n" + "=" * 50)
    print("📊 Summary")
    print("=" * 50)
    print(f"Available: {len(available)}")
    print(f"Missing: {len(missing)}")
    
    if missing:
        print(f"\n❌ Missing Dependencies:")
        for package in missing:
            print(f"  - {package}")
        
        print(f"\n💡 Installation Command:")
        print(f"pip install {' '.join(missing)}")
        
        print(f"\n🔧 Alternative (if using conda):")
        print(f"conda install {' '.join(missing)}")
        
        return 1
    else:
        print(f"\n✅ All dependencies are available!")
        return 0

if __name__ == "__main__":
    sys.exit(main())
