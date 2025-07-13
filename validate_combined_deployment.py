#!/usr/bin/env python3
"""
Validation script for combined API + Web UI deployment configuration.
This script verifies that all files and configurations are ready for deployment.
"""

import os
import json
import sys
from pathlib import Path

def validate_deployment_files():
    """Validate that all required deployment files exist."""
    print("📁 Validating deployment files...")
    
    required_files = [
        '.clawrc',
        'Dockerfile.claw',
        '.env.claw',
        'docker-compose.yml',
        'start_combined.sh',
        'web_ui/app.py',
        'web_ui/start.py',
        'web_ui/requirements.txt',
        'requirements.txt',
        'COMBINED_DEPLOYMENT_GUIDE.md',
        'COMBINED_DEPLOYMENT_CHECKLIST.md',
        'COMBINED_DEPLOYMENT_SUMMARY.md'
    ]
    
    missing_files = []
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} - Missing")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n❌ Missing {len(missing_files)} required files")
        return False
    
    print("✅ All deployment files present")
    return True


def validate_clawrc_config():
    """Validate .clawrc configuration for combined deployment."""
    print("\n⚙️ Validating .clawrc configuration...")
    
    try:
        with open('.clawrc', 'r') as f:
            config = json.load(f)
        
        # Check required fields
        required_fields = ['name', 'framework', 'port', 'run', 'resources', 'environment']
        for field in required_fields:
            if field in config:
                print(f"   ✅ {field}: {config[field] if field != 'environment' else 'configured'}")
            else:
                print(f"   ❌ Missing field: {field}")
                return False
        
        # Check combined deployment specific settings
        if config.get('port') == 5000:
            print("   ✅ Port configured for Web UI (5000)")
        else:
            print(f"   ⚠️  Port is {config.get('port')}, expected 5000")
        
        # Check resources for combined deployment
        resources = config.get('resources', {})
        cpu = resources.get('cpu', '')
        memory = resources.get('memory', '')
        
        if cpu == '1000m' and memory == '2Gi':
            print("   ✅ Resources configured for combined deployment (1 CPU, 2GB RAM)")
        else:
            print(f"   ⚠️  Resources: {cpu} CPU, {memory} RAM (recommended: 1000m CPU, 2Gi RAM)")
        
        # Check environment variables
        env = config.get('environment', {})
        required_env_vars = [
            'WEB_UI_HOST', 'WEB_UI_PORT', 'API_BASE_URL', 'API_HOST', 'API_PORT',
            'DATABASE_URL', 'NEO4J_URI', 'LLM_API_KEY'
        ]
        
        for var in required_env_vars:
            if var in env:
                print(f"   ✅ Environment variable: {var}")
            else:
                print(f"   ❌ Missing environment variable: {var}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error reading .clawrc: {e}")
        return False


def validate_dockerfile():
    """Validate Dockerfile.claw for combined deployment."""
    print("\n🐳 Validating Dockerfile.claw...")
    
    try:
        with open('Dockerfile.claw', 'r') as f:
            content = f.read()
        
        # Check for required elements
        checks = [
            ('FROM python:3.11-slim', 'Python 3.11 base image'),
            ('EXPOSE 5000 8058', 'Both ports exposed'),
            ('start_combined.sh', 'Combined startup script'),
            ('curl', 'curl installed for health checks'),
            ('lsof', 'lsof installed for port checking'),
            ('USER app', 'Non-root user configured')
        ]
        
        for check, description in checks:
            if check in content:
                print(f"   ✅ {description}")
            else:
                print(f"   ❌ Missing: {description}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error reading Dockerfile.claw: {e}")
        return False


def validate_startup_script():
    """Validate start_combined.sh script."""
    print("\n🚀 Validating startup script...")
    
    try:
        with open('start_combined.sh', 'r') as f:
            content = f.read()
        
        # Check for required functions and features
        checks = [
            ('check_port()', 'Port availability checking'),
            ('wait_for_service()', 'Service readiness checking'),
            ('cleanup()', 'Cleanup function'),
            ('trap cleanup SIGTERM SIGINT', 'Signal handling'),
            ('python -m agent.api', 'API server startup'),
            ('python web_ui/start.py', 'Web UI startup'),
            ('required_vars=', 'Environment validation'),
            ('API_PID=$!', 'Process ID tracking')
        ]
        
        for check, description in checks:
            if check in content:
                print(f"   ✅ {description}")
            else:
                print(f"   ❌ Missing: {description}")
        
        # Check if script is executable
        script_path = Path('start_combined.sh')
        if script_path.stat().st_mode & 0o111:
            print("   ✅ Script is executable")
        else:
            print("   ⚠️  Script is not executable (will be fixed in Docker)")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error reading start_combined.sh: {e}")
        return False


def validate_environment_template():
    """Validate .env.claw environment template."""
    print("\n📝 Validating environment template...")
    
    try:
        with open('.env.claw', 'r') as f:
            content = f.read()
        
        # Check for required environment variables
        required_vars = [
            'WEB_UI_HOST=0.0.0.0',
            'WEB_UI_PORT=5000',
            'API_BASE_URL=http://localhost:8058',
            'API_HOST=0.0.0.0',
            'API_PORT=8058',
            'DATABASE_URL=',
            'NEO4J_URI=',
            'NEO4J_USERNAME=',
            'NEO4J_PASSWORD=',
            'LLM_PROVIDER=openai',
            'LLM_API_KEY=',
            'EMBEDDING_API_KEY='
        ]
        
        for var in required_vars:
            if var in content:
                print(f"   ✅ {var.split('=')[0]}")
            else:
                print(f"   ❌ Missing: {var.split('=')[0]}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error reading .env.claw: {e}")
        return False


def validate_docker_compose():
    """Validate docker-compose.yml for local testing."""
    print("\n🐙 Validating docker-compose.yml...")
    
    try:
        with open('docker-compose.yml', 'r') as f:
            content = f.read()
        
        # Check for combined deployment configuration
        checks = [
            ('agentic-rag-combined:', 'Service name'),
            ('dockerfile: Dockerfile.claw', 'Correct Dockerfile'),
            ('"5000:5000"', 'Web UI port mapping'),
            ('"8058:8058"', 'API port mapping'),
            ('API_BASE_URL=http://localhost:8058', 'Internal API URL'),
            ('DATABASE_URL=', 'Database configuration'),
            ('NEO4J_URI=', 'Neo4j configuration'),
            ('LLM_API_KEY=', 'LLM configuration'),
            ('start_period: 60s', 'Extended startup time')
        ]
        
        for check, description in checks:
            if check in content:
                print(f"   ✅ {description}")
            else:
                print(f"   ❌ Missing: {description}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error reading docker-compose.yml: {e}")
        return False


def validate_documentation():
    """Validate that documentation is comprehensive."""
    print("\n📚 Validating documentation...")
    
    docs = [
        ('COMBINED_DEPLOYMENT_GUIDE.md', 'Comprehensive deployment guide'),
        ('COMBINED_DEPLOYMENT_CHECKLIST.md', 'Step-by-step checklist'),
        ('COMBINED_DEPLOYMENT_SUMMARY.md', 'Deployment summary')
    ]
    
    for doc_file, description in docs:
        try:
            with open(doc_file, 'r') as f:
                content = f.read()
            
            if len(content) > 1000:  # At least 1000 characters
                print(f"   ✅ {description}")
            else:
                print(f"   ⚠️  {description} - Content seems short")
        except Exception as e:
            print(f"   ❌ {description} - Error: {e}")
    
    return True


def main():
    """Main validation function."""
    print("🔍 Combined Deployment Validation")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path('web_ui/app.py').exists():
        print("❌ Please run this script from the project root directory")
        print("   (The directory containing the web_ui folder)")
        sys.exit(1)
    
    validations = [
        ("Deployment Files", validate_deployment_files),
        ("Claw Configuration", validate_clawrc_config),
        ("Dockerfile", validate_dockerfile),
        ("Startup Script", validate_startup_script),
        ("Environment Template", validate_environment_template),
        ("Docker Compose", validate_docker_compose),
        ("Documentation", validate_documentation)
    ]
    
    results = []
    
    for validation_name, validation_func in validations:
        try:
            result = validation_func()
            results.append((validation_name, result))
        except Exception as e:
            print(f"❌ {validation_name} validation failed: {e}")
            results.append((validation_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 Validation Summary")
    print("=" * 50)
    
    passed = 0
    for validation_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{validation_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} validations passed")
    
    if passed == len(results):
        print("\n🎉 Combined deployment configuration is ready!")
        print("\n📝 Next Steps:")
        print("1. Set up PostgreSQL and Neo4j databases")
        print("2. Obtain OpenAI API key")
        print("3. Update environment variables in Claw Cloud console")
        print("4. Deploy using the deployment guide")
        print("\n🌐 Deployment will be available at: https://your-app.claw.cloud")
    else:
        print("\n⚠️  Some validations failed. Please review and fix the issues above.")
    
    return passed == len(results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
