#!/usr/bin/env python3
"""
Environment variable validation script for Agentic RAG deployment.
"""

import os
import sys
from typing import List, Dict, Any

# Try to import dotenv, but don't fail if it's not available
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    def load_dotenv():
        """Fallback function when dotenv is not available."""
        pass

def validate_environment() -> Dict[str, Any]:
    """
    Validate all required environment variables.
    
    Returns:
        Dict with validation results
    """
    # Load .env file if it exists and dotenv is available
    if DOTENV_AVAILABLE:
        load_dotenv()
    else:
        print("⚠️  python-dotenv not available, relying on system environment variables")
    
    # Required environment variables
    required_vars = {
        # Database Configuration
        "DATABASE_URL": "PostgreSQL database connection URL",
        
        # Neo4j Configuration
        "NEO4J_URI": "Neo4j database URI (e.g., neo4j+s://instance.databases.neo4j.io)",
        "NEO4J_USERNAME": "Neo4j username (usually 'neo4j')",
        "NEO4J_PASSWORD": "Neo4j password",
        
        # LLM Configuration
        "LLM_API_KEY": "API key for LLM provider (OpenAI, etc.)",
        "EMBEDDING_API_KEY": "API key for embedding provider",
    }
    
    # Optional but recommended variables
    optional_vars = {
        "LLM_PROVIDER": "LLM provider (default: openai)",
        "LLM_CHOICE": "LLM model to use (default: gpt-4o-mini)",
        "EMBEDDING_MODEL": "Embedding model (default: text-embedding-3-small)",
        "LLM_BASE_URL": "LLM base URL (default: https://api.openai.com/v1)",
        "EMBEDDING_BASE_URL": "Embedding base URL (default: https://api.openai.com/v1)",
        "APP_ENV": "Application environment (default: production)",
        "LOG_LEVEL": "Logging level (default: INFO)",
    }
    
    results = {
        "valid": True,
        "missing_required": [],
        "missing_optional": [],
        "present_vars": [],
        "errors": []
    }
    
    print("🔍 Validating Environment Variables")
    print("=" * 50)
    
    # Check required variables
    print("\n📋 Required Variables:")
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if "API_KEY" in var or "PASSWORD" in var:
                display_value = f"{value[:8]}..." if len(value) > 8 else "***"
            else:
                display_value = value[:50] + "..." if len(value) > 50 else value
            
            print(f"   ✅ {var}: {display_value}")
            results["present_vars"].append(var)
        else:
            print(f"   ❌ {var}: NOT SET - {description}")
            results["missing_required"].append(var)
            results["valid"] = False
    
    # Check optional variables
    print("\n📋 Optional Variables:")
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if "API_KEY" in var or "PASSWORD" in var:
                display_value = f"{value[:8]}..." if len(value) > 8 else "***"
            else:
                display_value = value[:50] + "..." if len(value) > 50 else value
            
            print(f"   ✅ {var}: {display_value}")
            results["present_vars"].append(var)
        else:
            print(f"   ⚠️  {var}: NOT SET - {description}")
            results["missing_optional"].append(var)
    
    # Validation summary
    print("\n" + "=" * 50)
    if results["valid"]:
        print("✅ Environment validation PASSED")
        print(f"   Required variables: {len(required_vars) - len(results['missing_required'])}/{len(required_vars)}")
        print(f"   Optional variables: {len(optional_vars) - len(results['missing_optional'])}/{len(optional_vars)}")
    else:
        print("❌ Environment validation FAILED")
        print(f"   Missing required variables: {len(results['missing_required'])}")
        for var in results["missing_required"]:
            print(f"     - {var}")
    
    return results

def main():
    """Main function."""
    try:
        results = validate_environment()
        
        if not results["valid"]:
            print("\n🚨 Action Required:")
            print("Set the missing required environment variables and try again.")
            print("\nFor Docker deployment:")
            print("  - Set environment variables in your deployment platform")
            print("  - Or update the .env file and rebuild the container")
            print("\nFor local development:")
            print("  - Update the .env file in the project root")
            print("  - Or export the variables in your shell")
            
            sys.exit(1)
        else:
            print("\n🎉 Ready for deployment!")
            sys.exit(0)
            
    except Exception as e:
        print(f"\n❌ Validation failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
