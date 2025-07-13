#!/usr/bin/env python3
"""
Deployment script for deploying the Web UI to claw.cloud.
This script helps prepare and configure the deployment.
"""

import os
import json
import sys
from pathlib import Path

def create_claw_config():
    """Create claw.cloud configuration files."""
    print("📝 Creating claw.cloud configuration...")
    
    # Create .clawrc configuration
    claw_config = {
        "name": "agentic-rag-webui",
        "description": "Agentic RAG Web UI - Interactive chat interface for the knowledge graph system",
        "framework": "python",
        "python_version": "3.11",
        "build": {
            "commands": [
                "pip install --no-cache-dir -r requirements.txt",
                "pip install --no-cache-dir -r web_ui/requirements.txt"
            ]
        },
        "run": {
            "command": "python",
            "args": [
                "web_ui/start.py",
                "--host", "0.0.0.0",
                "--port", "5000",
                "--skip-health-check",
                "--production"
            ]
        },
        "port": 5000,
        "health_check": {
            "path": "/health",
            "port": 5000,
            "initial_delay_seconds": 30,
            "timeout_seconds": 10
        },
        "resources": {
            "cpu": "500m",
            "memory": "1Gi"
        },
        "scaling": {
            "min_replicas": 1,
            "max_replicas": 3
        },
        "environment": {
            "WEB_UI_HOST": "0.0.0.0",
            "WEB_UI_PORT": "5000",
            "API_BASE_URL": "https://your-api-server.claw.cloud",
            "APP_ENV": "production",
            "LOG_LEVEL": "INFO",
            "FLASK_ENV": "production"
        }
    }
    
    with open('.clawrc', 'w') as f:
        json.dump(claw_config, f, indent=2)
    
    print("✅ Created .clawrc configuration")
    return True

def create_deployment_dockerfile():
    """Create optimized Dockerfile for claw.cloud deployment."""
    print("🐳 Creating deployment Dockerfile...")
    
    dockerfile_content = '''# Optimized Dockerfile for claw.cloud deployment
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    curl \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
COPY web_ui/requirements.txt web_ui/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r web_ui/requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app
RUN chown -R app:app /app
USER app

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \\
    CMD curl -f http://localhost:5000/health || exit 1

# Start command
CMD ["python", "web_ui/start.py", "--host", "0.0.0.0", "--port", "5000", "--skip-health-check", "--production"]
'''
    
    with open('Dockerfile.claw', 'w') as f:
        f.write(dockerfile_content)
    
    print("✅ Created Dockerfile.claw")
    return True

def create_docker_compose():
    """Create docker-compose.yml for local testing."""
    print("🐙 Creating docker-compose.yml for local testing...")
    
    compose_content = '''version: '3.8'

services:
  webui:
    build:
      context: .
      dockerfile: Dockerfile.claw
    ports:
      - "5000:5000"
    environment:
      - WEB_UI_HOST=0.0.0.0
      - WEB_UI_PORT=5000
      - API_BASE_URL=https://your-api-server.claw.cloud
      - APP_ENV=production
      - LOG_LEVEL=INFO
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
    restart: unless-stopped
'''
    
    with open('docker-compose.yml', 'w') as f:
        f.write(compose_content)
    
    print("✅ Created docker-compose.yml")
    return True

def create_deployment_guide():
    """Create step-by-step deployment guide."""
    print("📚 Creating deployment guide...")
    
    guide_content = '''# 🚀 Deploy to Claw Cloud - Step by Step Guide

## Quick Deployment

### Option 1: Using Claw CLI (Recommended)

1. **Install Claw CLI:**
   ```bash
   npm install -g @claw/cli
   # or
   curl -sSL https://get.claw.cloud | bash
   ```

2. **Login to Claw:**
   ```bash
   claw login
   ```

3. **Deploy from this directory:**
   ```bash
   claw deploy
   ```

### Option 2: Using Web Console

1. **Go to [console.run.claw.cloud](https://console.run.claw.cloud)**

2. **Click "Deploy from Git"**

3. **Configure:**
   - Repository: Your GitHub repo URL
   - Branch: main
   - Build Context: /
   - Dockerfile: Dockerfile.claw

4. **Set Environment Variables:**
   ```
   WEB_UI_HOST=0.0.0.0
   WEB_UI_PORT=5000
   API_BASE_URL=https://your-api-server.claw.cloud
   APP_ENV=production
   LOG_LEVEL=INFO
   ```

5. **Deploy!**

## Configuration

### Required Environment Variables

```bash
# Web UI Configuration
WEB_UI_HOST=0.0.0.0
WEB_UI_PORT=5000

# API Server URL (update this!)
API_BASE_URL=https://your-api-server.claw.cloud

# Application Environment
APP_ENV=production
LOG_LEVEL=INFO
FLASK_ENV=production
```

### Optional Environment Variables

```bash
# Custom branding
APP_TITLE="Your Company RAG Assistant"
APP_DESCRIPTION="AI-powered knowledge assistant"

# Performance tuning
GUNICORN_WORKERS=4
GUNICORN_TIMEOUT=120
```

## Testing Your Deployment

### 1. Health Check
```bash
curl https://your-app.claw.cloud/health
```

### 2. Web Interface
Open `https://your-app.claw.cloud` in your browser

### 3. API Connectivity
Check the connection status in the web UI

## Troubleshooting

### Build Issues
- Ensure all requirements.txt files are present
- Check Python version compatibility
- Verify Dockerfile syntax

### Runtime Issues
- Check environment variables
- Verify API server is accessible
- Review application logs in claw console

### Performance Issues
- Monitor resource usage
- Adjust CPU/memory limits
- Enable auto-scaling

## Support

- Claw Cloud Docs: https://docs.run.claw.cloud
- GitHub Issues: Your repository issues page
'''
    
    with open('DEPLOY_TO_CLAW.md', 'w') as f:
        f.write(guide_content)
    
    print("✅ Created DEPLOY_TO_CLAW.md")
    return True

def validate_deployment_files():
    """Validate that all necessary files exist for deployment."""
    print("🔍 Validating deployment files...")
    
    required_files = [
        'web_ui/app.py',
        'web_ui/start.py',
        'web_ui/requirements.txt',
        'web_ui/templates/index.html',
        'web_ui/static/css/style.css',
        'web_ui/static/js/app.js',
        'requirements.txt'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
            print(f"   ❌ Missing: {file_path}")
        else:
            print(f"   ✅ Found: {file_path}")
    
    if missing_files:
        print(f"\n❌ Missing {len(missing_files)} required files")
        return False
    
    print("✅ All required files present")
    return True

def create_env_template():
    """Create environment template for claw.cloud."""
    print("⚙️ Creating environment template...")
    
    env_template = '''# Environment Variables for Claw Cloud Deployment
# Copy these to your claw.cloud environment configuration

# === REQUIRED VARIABLES ===

# Web UI Configuration
WEB_UI_HOST=0.0.0.0
WEB_UI_PORT=5000

# API Server URL - UPDATE THIS!
API_BASE_URL=https://your-api-server.claw.cloud

# Application Environment
APP_ENV=production
LOG_LEVEL=INFO
FLASK_ENV=production

# === OPTIONAL VARIABLES ===

# Custom Branding
# APP_TITLE="Your Company RAG Assistant"
# APP_DESCRIPTION="AI-powered knowledge assistant"

# Performance Tuning
# GUNICORN_WORKERS=4
# GUNICORN_TIMEOUT=120
# GUNICORN_MAX_REQUESTS=1000

# === NOTES ===
# 1. Update API_BASE_URL to point to your actual API server
# 2. For combined deployment, use: API_BASE_URL=http://localhost:8058
# 3. For external API, use: API_BASE_URL=https://your-api.claw.cloud
'''
    
    with open('.env.claw', 'w') as f:
        f.write(env_template)
    
    print("✅ Created .env.claw template")
    return True

def main():
    """Main deployment preparation function."""
    print("🚀 Preparing Web UI for Claw Cloud Deployment")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not Path('web_ui/app.py').exists():
        print("❌ Please run this script from the project root directory")
        print("   (The directory containing the web_ui folder)")
        sys.exit(1)
    
    tasks = [
        ("Validate Deployment Files", validate_deployment_files),
        ("Create Claw Configuration", create_claw_config),
        ("Create Deployment Dockerfile", create_deployment_dockerfile),
        ("Create Docker Compose", create_docker_compose),
        ("Create Environment Template", create_env_template),
        ("Create Deployment Guide", create_deployment_guide)
    ]
    
    results = []
    
    for task_name, task_func in tasks:
        try:
            result = task_func()
            results.append((task_name, result))
        except Exception as e:
            print(f"❌ {task_name} failed: {e}")
            results.append((task_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 Deployment Preparation Summary")
    print("=" * 60)
    
    passed = 0
    for task_name, result in results:
        status = "✅ COMPLETED" if result else "❌ FAILED"
        print(f"{task_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tasks completed")
    
    if passed == len(results):
        print("\n🎉 Deployment preparation complete!")
        print("\n📝 Next Steps:")
        print("1. Update API_BASE_URL in .env.claw")
        print("2. Review DEPLOY_TO_CLAW.md for deployment instructions")
        print("3. Deploy using: claw deploy")
        print("   Or use the web console at console.run.claw.cloud")
        print("\n🌐 Files created:")
        print("   - .clawrc (claw configuration)")
        print("   - Dockerfile.claw (optimized dockerfile)")
        print("   - docker-compose.yml (local testing)")
        print("   - .env.claw (environment template)")
        print("   - DEPLOY_TO_CLAW.md (deployment guide)")
    else:
        print("\n⚠️  Some tasks failed. Check the output above.")
    
    return passed == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
